import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, text
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
    open_incidents = session.scalar(
        select(func.count(Incident.id)).where(Incident.status.in_(["OPEN", "ACKNOWLEDGED"]))
    )
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
        "open_incidents": int(open_incidents or 0),
    }
