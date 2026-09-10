from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ServiceCheck(Base):
    __tablename__ = "service_checks"
    __table_args__ = (
        Index("ix_service_checks_status_checked_at", "status", "checked_at"),
        Index("ix_service_checks_service_checked_at", "service_name", "checked_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_name: Mapped[str] = mapped_column(String(120), index=True)
    check_type: Mapped[str] = mapped_column(String(80), index=True)
    target: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    response_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_status_severity", "status", "severity"),
        Index("ix_incidents_service_detected", "service_name", "detected_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_incident_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(128), index=True)
    service_name: Mapped[str] = mapped_column(String(120), index=True)
    short_description: Mapped[str] = mapped_column(String(500))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    impact: Mapped[str] = mapped_column(String(20))
    urgency: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), index=True)
    detection_source: Mapped[str] = mapped_column(String(80), default="synthetic-monitor")
    diagnostic_summary: Mapped[str] = mapped_column(Text, default="")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    root_cause: Mapped[str | None] = mapped_column(Text)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    recovery_successes: Mapped[int] = mapped_column(Integer, default=0)
    corrective_actions: Mapped[list["CorrectiveAction"]] = relationship(back_populates="incident")


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"
    __table_args__ = (Index("ix_deployments_environment_started", "environment", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(80))
    commit_sha: Mapped[str] = mapped_column(String(64), index=True)
    environment: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    pipeline_url: Mapped[str | None] = mapped_column(String(1000))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    action: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(120))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), index=True)
    verification_evidence: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    incident: Mapped[Incident] = relationship(back_populates="corrective_actions")
