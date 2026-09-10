CREATE TABLE IF NOT EXISTS service_checks (
    id BIGSERIAL PRIMARY KEY,
    service_name VARCHAR(120) NOT NULL,
    check_type VARCHAR(80) NOT NULL,
    target VARCHAR(500) NOT NULL,
    status VARCHAR(30) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    response_ms DOUBLE PRECISION,
    status_code INTEGER,
    details_json TEXT NOT NULL DEFAULT '{}',
    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_service_checks_status_checked_at
    ON service_checks (status, checked_at DESC);

CREATE TABLE IF NOT EXISTS incidents (
    id BIGSERIAL PRIMARY KEY,
    external_incident_id VARCHAR(120),
    dedupe_key VARCHAR(128) NOT NULL,
    service_name VARCHAR(120) NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    impact VARCHAR(20) NOT NULL,
    urgency VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,
    detection_source VARCHAR(80) NOT NULL,
    diagnostic_summary TEXT NOT NULL DEFAULT '',
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    root_cause TEXT,
    resolution_notes TEXT,
    recovery_successes INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_incidents_status_severity
    ON incidents (status, severity);

CREATE TABLE IF NOT EXISTS deployment_events (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(80) NOT NULL,
    commit_sha VARCHAR(64) NOT NULL,
    environment VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL,
    pipeline_url VARCHAR(1000),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS corrective_actions (
    id BIGSERIAL PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES incidents(id),
    action TEXT NOT NULL,
    owner VARCHAR(120) NOT NULL,
    due_date TIMESTAMPTZ,
    status VARCHAR(30) NOT NULL,
    verification_evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

