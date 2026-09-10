from fastapi.testclient import TestClient


def monitor_payload(healthy: bool, status_code: int) -> dict[str, object]:
    return {
        "service_name": "production-reliability-platform",
        "check_type": "synthetic-end-to-end",
        "target": "https://example.test",
        "healthy": healthy,
        "status_code": status_code,
        "response_ms": 125.5,
        "dns_addresses": ["192.0.2.10"],
        "tls_days_remaining": 90,
        "diagnostic_summary": "all checks passed" if healthy else "readiness returned 503",
    }


def test_failed_checks_create_then_update_one_incident(client: TestClient) -> None:
    created = client.post("/api/checks", json=monitor_payload(False, 503))
    updated = client.post("/api/checks", json=monitor_payload(False, 503))
    incidents = client.get("/api/incidents")

    assert created.status_code == 200
    assert created.json()["incident_action"] == "created"
    assert created.json()["severity"] == "HIGH"
    assert updated.json()["incident_action"] == "updated"
    assert updated.json()["incident_id"] == created.json()["incident_id"]
    assert len(incidents.json()) == 1


def test_incident_resolves_after_consecutive_recovery_checks(client: TestClient) -> None:
    failed = client.post("/api/checks", json=monitor_payload(False, 503)).json()
    first = client.post("/api/checks", json=monitor_payload(True, 200)).json()
    second = client.post("/api/checks", json=monitor_payload(True, 200)).json()
    incident = client.get(f"/api/incidents/{failed['incident_id']}").json()

    assert first["incident_action"] == "recovery_pending"
    assert first["recovery_successes"] == 1
    assert second["incident_action"] == "resolved"
    assert incident["status"] == "RESOLVED"
    assert incident["resolved_at"] is not None


def test_healthy_check_without_incident_requires_no_action(client: TestClient) -> None:
    response = client.post("/api/checks", json=monitor_payload(True, 200))

    assert response.status_code == 200
    assert response.json()["incident_action"] == "none"
    assert response.json()["incident_id"] is None


def test_incident_status_filter(client: TestClient) -> None:
    client.post("/api/checks", json=monitor_payload(False, 503))

    assert len(client.get("/api/incidents?status=open").json()) == 1
    assert client.get("/api/incidents?status=resolved").json() == []


def test_missing_incident_returns_404(client: TestClient) -> None:
    response = client.get("/api/incidents/9999")

    assert response.status_code == 404
