from fastapi.testclient import TestClient


def test_root_redirects_to_dashboard(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_dashboard_page_and_assets_are_served(client: TestClient) -> None:
    page = client.get("/dashboard")
    stylesheet = client.get("/dashboard-assets/styles.css")
    script = client.get("/dashboard-assets/dashboard.js")

    assert page.status_code == 200
    assert "Reliability Control Room" in page.text
    assert "/api/dashboard" in script.text
    assert stylesheet.status_code == 200
    assert script.status_code == 200


def test_health_contract(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["environment"] == "test"
    assert response.headers["x-request-id"]


def test_readiness_records_database_check(client: TestClient) -> None:
    response = client.get("/readyz")
    status = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["database"] == "available"
    assert status.json()["last_check"]["type"] == "database-readiness"
    assert status.json()["last_check"]["status"] == "HEALTHY"


def test_dashboard_data_summarises_operational_checks(client: TestClient) -> None:
    client.get("/readyz")
    dashboard = client.get("/api/dashboard")

    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["state"] == "operational"
    assert payload["environment"] == "test"
    assert payload["check_pass_rate_percent"] == 100.0
    assert payload["open_incidents"] == 0
    assert payload["open_incidents_by_severity"] == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    assert payload["recent_checks"][0]["check_type"] == "database-readiness"


def test_metrics_expose_required_series(client: TestClient) -> None:
    client.get("/healthz")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "reliability_http_requests_total" in response.text
    assert "reliability_readiness_state" in response.text
    assert "reliability_build_info" in response.text


def test_fault_injection_requires_token(client: TestClient) -> None:
    response = client.post("/ops/faults/readiness")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"


def test_controlled_readiness_failure_and_recovery(client: TestClient) -> None:
    headers = {"x-admin-token": "test-admin-token"}

    activated = client.post("/ops/faults/readiness", headers=headers)
    failed = client.get("/readyz")
    recovered = client.post("/ops/recover", headers=headers)
    ready = client.get("/readyz")

    assert activated.status_code == 200
    assert failed.status_code == 503
    assert failed.json()["diagnostic_code"] == "CONTROLLED_READINESS_FAILURE"
    assert recovered.status_code == 200
    assert ready.status_code == 200


def test_controlled_error_affects_status_not_health(client: TestClient) -> None:
    headers = {"x-admin-token": "test-admin-token"}
    client.post("/ops/faults/error", headers=headers)

    assert client.get("/healthz").status_code == 200
    assert client.get("/api/status").status_code == 500
