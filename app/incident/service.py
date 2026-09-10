import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import MonitorCheckRequest
from app.core.config import Settings
from app.db.models import Incident
from app.db.repository import record_check
from app.incident.adapters import ExternalIncidentClient, ExternalIncidentPayload


@dataclass(frozen=True)
class IncidentProcessResult:
    check_id: int
    severity: str
    action: str
    incident: Incident | None


_SEVERITY_ORDER = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}


def incident_dedupe_key(check: MonitorCheckRequest) -> str:
    value = f"{check.service_name}|{check.check_type}|{check.target}".lower()
    return hashlib.sha256(value.encode()).hexdigest()


def classify_severity(check: MonitorCheckRequest) -> str:
    if not check.healthy and (check.status_code is None or check.status_code >= 500):
        return "HIGH"
    if check.tls_days_remaining is not None and check.tls_days_remaining < 15:
        return "HIGH"
    if not check.healthy:
        return "MEDIUM"
    return "NONE"


def _impact_urgency(severity: str) -> tuple[str, str]:
    if severity == "HIGH":
        return "HIGH", "HIGH"
    if severity == "MEDIUM":
        return "MEDIUM", "MEDIUM"
    return "LOW", "LOW"


def _open_incident(session: Session, dedupe_key: str) -> Incident | None:
    return session.scalar(
        select(Incident)
        .where(
            Incident.dedupe_key == dedupe_key,
            Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
        )
        .order_by(Incident.detected_at.desc())
        .limit(1)
    )


def _payload(incident: Incident) -> ExternalIncidentPayload:
    return ExternalIncidentPayload(
        short_description=incident.short_description,
        service_name=incident.service_name,
        severity=incident.severity,
        impact=incident.impact,
        urgency=incident.urgency,
        diagnostic_summary=incident.diagnostic_summary,
        dedupe_key=incident.dedupe_key,
    )


def process_monitor_check(
    session: Session,
    check: MonitorCheckRequest,
    settings: Settings,
    external_client: ExternalIncidentClient,
) -> IncidentProcessResult:
    severity = classify_severity(check)
    stored_check = record_check(
        session,
        service_name=check.service_name,
        check_type=check.check_type,
        target=check.target,
        status="HEALTHY" if check.healthy else "FAILED",
        severity=severity,
        response_ms=check.response_ms,
        status_code=check.status_code,
        details={
            "dns_addresses": check.dns_addresses,
            "tls_days_remaining": check.tls_days_remaining,
            "diagnostic_summary": check.diagnostic_summary,
            "observed_at": check.observed_at,
        },
    )
    dedupe_key = incident_dedupe_key(check)
    incident = _open_incident(session, dedupe_key)

    if not check.healthy:
        impact, urgency = _impact_urgency(severity)
        if incident is None:
            incident = Incident(
                dedupe_key=dedupe_key,
                service_name=check.service_name,
                short_description=f"{check.check_type} failure for {check.service_name}",
                severity=severity,
                impact=impact,
                urgency=urgency,
                status="OPEN",
                detection_source="powershell-synthetic-monitor",
                diagnostic_summary=check.diagnostic_summary,
            )
            session.add(incident)
            session.flush()
            incident.external_incident_id = external_client.create_incident(_payload(incident))
            action = "created"
        else:
            if _SEVERITY_ORDER[severity] > _SEVERITY_ORDER[incident.severity]:
                incident.severity = severity
                incident.impact = impact
                incident.urgency = urgency
            incident.diagnostic_summary = check.diagnostic_summary
            incident.recovery_successes = 0
            if incident.external_incident_id:
                external_client.update_incident(incident.external_incident_id, _payload(incident))
            action = "updated"
        session.commit()
        session.refresh(incident)
        return IncidentProcessResult(stored_check.id, severity, action, incident)

    if incident is None:
        return IncidentProcessResult(stored_check.id, severity, "none", None)

    incident.recovery_successes += 1
    if incident.recovery_successes >= settings.recovery_success_threshold:
        incident.status = "RESOLVED"
        incident.resolved_at = datetime.now(UTC)
        incident.resolution_notes = (
            f"Resolved after {incident.recovery_successes} consecutive healthy checks."
        )
        if incident.external_incident_id:
            external_client.resolve_incident(
                incident.external_incident_id,
                incident.resolution_notes,
            )
        action = "resolved"
    else:
        action = "recovery_pending"
    session.commit()
    session.refresh(incident)
    return IncidentProcessResult(stored_check.id, severity, action, incident)
