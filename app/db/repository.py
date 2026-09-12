import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import DeploymentEvent, Incident, ServiceCheck


def database_health(session: Session) -> float:
    started = datetime.now(UTC)
    session.execute(text("SELECT 1"))
    elapsed = datetime.now(UTC) - started
    return round(elapsed.total_seconds() * 1000, 3)


def record_check(
    session: Session,
    *,
    service_name: str,
    check_type: str,
    target: str,
    status: str,
    severity: str,
    response_ms: float | None = None,
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
) -> ServiceCheck:
    check = ServiceCheck(
        service_name=service_name,
        check_type=check_type,
        target=target,
        status=status,
        severity=severity,
        response_ms=response_ms,
        status_code=status_code,
        details_json=json.dumps(details or {}, default=str),
    )
    session.add(check)
    session.commit()
    session.refresh(check)
    return check


def status_summary(session: Session) -> dict[str, Any]:
    latest_check = session.scalar(
        select(ServiceCheck).order_by(ServiceCheck.checked_at.desc()).limit(1)
    )
    latest_deployment = session.scalar(
        select(DeploymentEvent).order_by(DeploymentEvent.started_at.desc()).limit(1)
    )
    open_incidents = session.scalars(
        select(Incident).where(Incident.status.in_(["OPEN", "ACKNOWLEDGED"]))
    ).all()
    return {
        "last_check": None
        if latest_check is None
        else {
            "type": latest_check.check_type,
            "status": latest_check.status,
            "severity": latest_check.severity,
            "checked_at": latest_check.checked_at,
        },
        "last_deployment": None
        if latest_deployment is None
        else {
            "version": latest_deployment.version,
            "commit_sha": latest_deployment.commit_sha,
            "status": latest_deployment.status,
            "started_at": latest_deployment.started_at,
        },
        "open_incidents": len(open_incidents),
    }


def _aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def dashboard_summary(session: Session) -> dict[str, Any]:
    """Return a bounded, presentation-ready operational summary."""
    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=24)
    recent_checks = list(
        session.scalars(
            select(ServiceCheck).order_by(ServiceCheck.checked_at.desc()).limit(40)
        ).all()
    )
    recent_incidents = list(
        session.scalars(select(Incident).order_by(Incident.detected_at.desc()).limit(12)).all()
    )
    latest_deployment = session.scalar(
        select(DeploymentEvent).order_by(DeploymentEvent.started_at.desc()).limit(1)
    )

    checks_24h = [check for check in recent_checks if _aware_utc(check.checked_at) >= cutoff]
    availability_checks = [
        check
        for check in checks_24h
        if check.status in {"HEALTHY", "FAILED", "CRITICAL", "WARNING"}
    ]
    healthy_checks = [check for check in availability_checks if check.status == "HEALTHY"]
    latency_values = [
        check.response_ms
        for check in checks_24h
        if check.response_ms is not None and check.status != "ACTIVATED"
    ]
    resolved_incidents = [
        incident
        for incident in recent_incidents
        if incident.resolved_at is not None
    ]
    mttr_values = [
        (_aware_utc(incident.resolved_at) - _aware_utc(incident.detected_at)).total_seconds()
        for incident in resolved_incidents
        if incident.resolved_at is not None
    ]
    open_incidents = [
        incident for incident in recent_incidents if incident.status in {"OPEN", "ACKNOWLEDGED"}
    ]
    severity_counts = {
        severity: sum(incident.severity == severity for incident in open_incidents)
        for severity in ("HIGH", "MEDIUM", "LOW")
    }

    return {
        "generated_at": now,
        "window_hours": 24,
        "check_pass_rate_percent": (
            round(len(healthy_checks) / len(availability_checks) * 100, 2)
            if availability_checks
            else None
        ),
        "average_response_ms": (
            round(sum(latency_values) / len(latency_values), 2) if latency_values else None
        ),
        "average_mttr_seconds": round(sum(mttr_values) / len(mttr_values), 2)
        if mttr_values
        else None,
        "open_incidents": len(open_incidents),
        "open_incidents_by_severity": severity_counts,
        "latest_deployment": None
        if latest_deployment is None
        else {
            "version": latest_deployment.version,
            "commit_sha": latest_deployment.commit_sha,
            "environment": latest_deployment.environment,
            "status": latest_deployment.status,
            "pipeline_url": latest_deployment.pipeline_url,
            "started_at": latest_deployment.started_at,
            "completed_at": latest_deployment.completed_at,
        },
        "recent_checks": [
            {
                "id": check.id,
                "check_type": check.check_type,
                "target": check.target,
                "status": check.status,
                "severity": check.severity,
                "response_ms": check.response_ms,
                "status_code": check.status_code,
                "checked_at": check.checked_at,
            }
            for check in recent_checks
        ],
        "recent_incidents": [
            {
                "id": incident.id,
                "external_incident_id": incident.external_incident_id,
                "short_description": incident.short_description,
                "severity": incident.severity,
                "status": incident.status,
                "detection_source": incident.detection_source,
                "detected_at": incident.detected_at,
                "resolved_at": incident.resolved_at,
                "recovery_successes": incident.recovery_successes,
            }
            for incident in recent_incidents
        ],
    }
