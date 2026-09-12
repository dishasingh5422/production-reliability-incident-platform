# Operations runbook

**Service:** Production Reliability Platform  
**Purpose:** Consistent triage, recovery, verification, and escalation during the portfolio simulation

## 1. Confirm the signal

1. Record alert time, target, check type, response code, latency, and correlation key.
2. Call `/healthz`, `/readyz`, `/api/status`, and `/api/incidents?status=open`.
3. Do not restart or roll back until the failure layer is identified.

## 2. Interpret health and readiness

| Health | Readiness | Interpretation | First action |
|---|---|---|---|
| 200 | 200 | Service available | Check latency and intermittent signals |
| 200 | 503 | Process alive; dependency/readiness failing | Check PostgreSQL, configuration, and drill state |
| No response | No response | Process, network, DNS, or platform failure | Check DNS, port, container, revision, and platform events |
| 200 | 200 but slow | Degraded performance | Review latency, logs, saturation, and recent deployment |

## 3. Networking diagnostics

- Resolve the hostname and compare returned addresses with the target.
- Confirm TCP connection to port 443 or the configured port.
- Verify TLS hostname and days to expiry.
- Confirm status and latency from another location when possible.
- For Cloud Run, verify ingress, invocation policy, service URL, and traffic revision.

## 4. Application and database diagnostics

- Use `x-request-id` to correlate requests and structured logs.
- Review version and environment from `/healthz`.
- Review HTTP errors and latency in `/metrics`.
- `DATABASE_UNAVAILABLE` means a real SQL connection failure.
- `CONTROLLED_READINESS_FAILURE` identifies the deliberate drill.
- Confirm the PostgreSQL container is healthy without printing credentials.
- Do not delete the PostgreSQL volume during triage.

## 5. Severity

| Severity | Condition | Response target in simulation |
|---|---|---|
| High | No response, HTTP 5xx, readiness failure, or TLS under 15 days | Immediate triage |
| Medium | Other failed check or material latency | Same-session investigation |
| Low | Informational degradation | Track and improve |

## 6. Recovery order

1. Remove a controlled fault only when its diagnostic code proves a drill.
2. Correct dependency or configuration availability.
3. If failure followed a release, route traffic to the last known good revision.
4. Restart only the smallest affected component when justified.
5. Never destroy persistent data as a shortcut.

## 7. Verify and close

- Require two consecutive healthy results.
- Confirm health, readiness, and normal latency.
- Confirm the same incident resolves rather than duplicates.
- Record timestamps, root cause, and preventive action.
- Update a test, alert, or runbook step.

