import logging
import time
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.core.config import Settings, get_settings
from app.core.faults import fault_controller
from app.db.base import get_session
from app.db.repository import database_health, record_check, status_summary
from app.monitoring.metrics import DATABASE_CHECK_DURATION, READINESS_STATE

router = APIRouter()
logger = logging.getLogger(__name__)
SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def require_fault_access(
    settings: SettingsDependency,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.enable_fault_injection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="fault injection disabled",
        )
    expected = settings.fault_admin_token.get_secret_value()
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin token")


FaultAccess = Annotated[None, Depends(require_fault_access)]


@router.get("/healthz", tags=["operations"])
def health(settings: SettingsDependency) -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/readyz", tags=["operations"])
def readiness(session: SessionDependency, settings: SettingsDependency) -> Response:
    fault = fault_controller.snapshot()
    if fault.mode == "readiness":
        READINESS_STATE.set(0)
        record_check(
            session,
            service_name=settings.app_name,
            check_type="database-readiness",
            target="database",
            status="CRITICAL",
            severity="HIGH",
            status_code=503,
            details={"diagnostic_code": "CONTROLLED_READINESS_FAILURE"},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "diagnostic_code": "CONTROLLED_READINESS_FAILURE"},
        )
    try:
        duration_ms = database_health(session)
    except SQLAlchemyError:
        logger.exception("database readiness check failed")
        READINESS_STATE.set(0)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "diagnostic_code": "DATABASE_UNAVAILABLE"},
        )
    READINESS_STATE.set(1)
    DATABASE_CHECK_DURATION.set(duration_ms)
    record_check(
        session,
        service_name=settings.app_name,
        check_type="database-readiness",
        target="database",
        status="HEALTHY",
        severity="NONE",
        response_ms=duration_ms,
        status_code=200,
    )
    return JSONResponse(
        content={"status": "ready", "database": "available", "duration_ms": duration_ms}
    )


@router.get("/metrics", tags=["operations"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/api/status", tags=["operations"])
def application_status(
    session: SessionDependency,
    settings: SettingsDependency,
) -> dict[str, object]:
    fault = fault_controller.snapshot()
    if fault.mode == "error":
        raise HTTPException(status_code=500, detail="controlled application error")
    if fault.mode == "latency" and fault.latency_ms:
        time.sleep(fault.latency_ms / 1000)
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "state": "operational" if fault.mode is None else "degraded",
        "fault_mode": fault.mode,
        **status_summary(session),
    }


@router.post("/ops/faults/{mode}", tags=["incident-drill"])
def activate_fault(
    mode: Literal["latency", "error", "readiness"],
    _: FaultAccess,
    session: SessionDependency,
    settings: SettingsDependency,
    latency_ms: Annotated[int, Query(ge=100, le=10_000)] = 1500,
) -> dict[str, object]:
    state = fault_controller.activate(mode, latency_ms if mode == "latency" else 0)
    record_check(
        session,
        service_name=settings.app_name,
        check_type="fault-injection",
        target=mode,
        status="ACTIVATED",
        severity="HIGH" if mode != "latency" else "MEDIUM",
        details={"mode": mode, "latency_ms": state["latency_ms"]},
    )
    logger.warning("controlled fault activated", extra={"context": {"mode": mode}})
    return {"status": "fault_active", "fault": state}


@router.post("/ops/recover", tags=["incident-drill"])
def recover(
    _: FaultAccess,
    session: SessionDependency,
    settings: SettingsDependency,
) -> dict[str, object]:
    previous = fault_controller.recover()
    record_check(
        session,
        service_name=settings.app_name,
        check_type="fault-injection",
        target=str(previous.get("mode") or "none"),
        status="RECOVERED",
        severity="NONE",
        details={"previous": previous},
    )
    logger.info("controlled fault recovered", extra={"context": {"previous": previous}})
    return {"status": "recovered", "previous_fault": previous}
