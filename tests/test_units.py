import json

import httpx
from pydantic import SecretStr

from app.api.schemas import MonitorCheckRequest
from app.core.config import Settings
from app.core.logging import JsonFormatter, redact
from app.incident.adapters import ExternalIncidentPayload, ServiceNowIncidentClient
from app.incident.service import classify_severity, incident_dedupe_key


def test_dedupe_key_is_deterministic_and_case_insensitive() -> None:
    first = MonitorCheckRequest(
        service_name="Service-A",
        check_type="HTTP",
        target="HTTPS://EXAMPLE.TEST",
        healthy=False,
    )
    second = MonitorCheckRequest(
        service_name="service-a",
        check_type="http",
        target="https://example.test",
        healthy=False,
    )

    assert incident_dedupe_key(first) == incident_dedupe_key(second)
    assert len(incident_dedupe_key(first)) == 64


def test_severity_mapping() -> None:
    assert (
        classify_severity(
            MonitorCheckRequest(
                service_name="api", check_type="http", target="test", healthy=False, status_code=503
            )
        )
        == "HIGH"
    )
    assert (
        classify_severity(
            MonitorCheckRequest(
                service_name="api", check_type="http", target="test", healthy=False, status_code=429
            )
        )
        == "MEDIUM"
    )
    assert (
        classify_severity(
            MonitorCheckRequest(service_name="api", check_type="http", target="test", healthy=True)
        )
        == "NONE"
    )


def test_recursive_secret_redaction() -> None:
    value = {"username": "operator", "password": "unsafe", "nested": {"token": "unsafe"}}

    assert redact(value) == {
        "username": "operator",
        "password": "[REDACTED]",
        "nested": {"token": "[REDACTED]"},
    }


def test_json_formatter_emits_valid_json_without_secret() -> None:
    import logging

    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    record.context = {"password": "unsafe", "status": "healthy"}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["context"]["password"] == "[REDACTED]"
    assert "unsafe" not in json.dumps(payload)


def test_servicenow_adapter_payload_and_identifier() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/now/table/incident"
        body = json.loads(request.content)
        assert body["short_description"] == "Readiness failed"
        assert body["impact"] == "1"
        assert "secret" not in request.content.decode().lower()
        return httpx.Response(201, json={"result": {"sys_id": "abc123", "number": "INC001"}})

    settings = Settings(
        incident_provider="servicenow",
        servicenow_instance_url="https://instance.example.test",
        servicenow_username="operator",
        servicenow_password=SecretStr("secret-value"),
    )
    client = ServiceNowIncidentClient(settings, transport=httpx.MockTransport(handler))
    payload = ExternalIncidentPayload(
        short_description="Readiness failed",
        service_name="service-a",
        severity="HIGH",
        impact="HIGH",
        urgency="HIGH",
        diagnostic_summary="HTTP 503",
        dedupe_key="abc",
    )

    assert client.create_incident(payload) == "abc123"
