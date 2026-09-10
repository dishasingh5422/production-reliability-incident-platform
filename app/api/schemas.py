from datetime import datetime

from pydantic import BaseModel, Field


class MonitorCheckRequest(BaseModel):
    service_name: str = Field(min_length=1, max_length=120)
    check_type: str = Field(min_length=1, max_length=80)
    target: str = Field(min_length=1, max_length=500)
    healthy: bool
    status_code: int | None = Field(default=None, ge=100, le=599)
    response_ms: float | None = Field(default=None, ge=0)
    dns_addresses: list[str] = Field(default_factory=list)
    tls_days_remaining: float | None = None
    diagnostic_summary: str = Field(default="", max_length=4000)
    observed_at: datetime | None = None


class MonitorCheckResponse(BaseModel):
    check_id: int
    severity: str
    incident_action: str
    incident_id: int | None
    external_incident_id: str | None
    recovery_successes: int


class IncidentResponse(BaseModel):
    id: int
    external_incident_id: str | None
    dedupe_key: str
    service_name: str
    short_description: str
    severity: str
    impact: str
    urgency: str
    status: str
    detection_source: str
    diagnostic_summary: str
    detected_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    recovery_successes: int

    model_config = {"from_attributes": True}
