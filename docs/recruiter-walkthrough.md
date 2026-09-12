# Recruiter walkthrough

## Three-minute version

> I built a Production Reliability and Incident Automation Platform to demonstrate the complete support lifecycle. Its live control-room dashboard shows service state, synthetic-check pass rate, response-time trends, open incidents, MTTR, deployment evidence, and recent monitoring checks. The Python service separates liveness from database readiness, exports metrics, stores checks and incidents in SQL, and provides guarded failure modes.
>
> A PowerShell monitor checks DNS, HTTP, TLS lifetime, latency, health, and readiness. A deterministic key prevents duplicate incidents, and recovery needs two consecutive successful checks.
>
> I validated it with 19 tests and 93% coverage, strict type and security checks, Docker Compose with PostgreSQL, a full dashboard-aware smoke test, and successful GitHub CI. In the controlled drill, PowerShell detected a 503, created one high-severity incident, and resolved it after recovery. The local simulation measured about 1.37 seconds to detect and 2.96 seconds to recover.
>
> Jenkins, GitLab, Cloud Run/Monitoring, rollback, and ServiceNow assets are implemented, but I label them pending until executed in authenticated environments rather than presenting configuration as production evidence.

## Demonstration order

1. Open `/dashboard` and explain the live state and metric boundaries.
2. Show the response-time chart, incident history, and Attention filter.
3. Show health, readiness, metrics, and status endpoints.
4. Explain the PowerShell monitor and deduplication logic.
5. Open the RCA timeline, Jenkins gates, and rollback procedure.
6. Close with the evidence map and pending live integrations.
