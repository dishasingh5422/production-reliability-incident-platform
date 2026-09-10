from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class ExternalIncidentPayload:
    short_description: str
    service_name: str
    severity: str
    impact: str
    urgency: str
    diagnostic_summary: str
    dedupe_key: str


class ExternalIncidentClient(Protocol):
    def create_incident(self, payload: ExternalIncidentPayload) -> str | None: ...

    def update_incident(self, external_id: str, payload: ExternalIncidentPayload) -> None: ...

    def resolve_incident(self, external_id: str, resolution_notes: str) -> None: ...


class MockIncidentClient:
    """Deterministic adapter used for local and automated verification."""

    def create_incident(self, payload: ExternalIncidentPayload) -> str:
        return f"MOCK-{payload.dedupe_key[:12].upper()}"

    def update_incident(self, external_id: str, payload: ExternalIncidentPayload) -> None:
        del external_id, payload

    def resolve_incident(self, external_id: str, resolution_notes: str) -> None:
        del external_id, resolution_notes


class ServiceNowIncidentClient:
    """Minimal ServiceNow Table API adapter; requires a configured developer instance."""

    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None) -> None:
        if not (
            settings.servicenow_instance_url
            and settings.servicenow_username
            and settings.servicenow_password
        ):
            raise ValueError("ServiceNow provider selected but credentials are incomplete")
        self._base_url = settings.servicenow_instance_url.rstrip("/")
        self._client = httpx.Client(
            auth=(
                settings.servicenow_username,
                settings.servicenow_password.get_secret_value(),
            ),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15.0,
            transport=transport,
        )

    @staticmethod
    def _priority_value(value: str) -> str:
        return {"HIGH": "1", "MEDIUM": "2", "LOW": "3"}.get(value, "3")

    def _payload(self, payload: ExternalIncidentPayload) -> dict[str, Any]:
        return {
            "short_description": payload.short_description,
            "description": (
                f"Service: {payload.service_name}\n"
                f"Deduplication key: {payload.dedupe_key}\n"
                f"Diagnostics: {payload.diagnostic_summary}"
            ),
            "impact": self._priority_value(payload.impact),
            "urgency": self._priority_value(payload.urgency),
            "category": "software",
        }

    def create_incident(self, payload: ExternalIncidentPayload) -> str:
        response = self._client.post(
            f"{self._base_url}/api/now/table/incident",
            json=self._payload(payload),
        )
        response.raise_for_status()
        result = response.json().get("result", {})
        identifier = result.get("sys_id") or result.get("number")
        if not identifier:
            raise RuntimeError("ServiceNow response did not contain an incident identifier")
        return str(identifier)

    def update_incident(self, external_id: str, payload: ExternalIncidentPayload) -> None:
        response = self._client.patch(
            f"{self._base_url}/api/now/table/incident/{external_id}",
            json={**self._payload(payload), "state": "2"},
        )
        response.raise_for_status()

    def resolve_incident(self, external_id: str, resolution_notes: str) -> None:
        response = self._client.patch(
            f"{self._base_url}/api/now/table/incident/{external_id}",
            json={
                "state": "6",
                "close_code": "Solved (Permanently)",
                "close_notes": resolution_notes,
            },
        )
        response.raise_for_status()


def build_external_client(settings: Settings) -> ExternalIncidentClient:
    if settings.incident_provider.lower() == "servicenow":
        return ServiceNowIncidentClient(settings)
    return MockIncidentClient()
