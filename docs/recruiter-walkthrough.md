# Recruiter walkthrough

## Three-minute version

> I built a Production Reliability and Incident Automation Platform to demonstrate the complete support lifecycle. The Python service separates liveness from database readiness, exports metrics, stores checks and incidents in SQL, and provides guarded failure modes.
>
> A PowerShell monitor checks DNS, HTTP, TLS lifetime, latency, health, and readiness. A deterministic key prevents duplicate incidents, and recovery needs two consecutive successful checks.
>
> I validated it with 16 tests and 93% coverage, strict type and security checks, Docker Compose with PostgreSQL, a full smoke test, and successful GitHub CI. In the controlled drill, PowerShell detected a 503, created one high-severity incident, and resolved it after recovery. The local simulation measured about 1.37 seconds to detect and 2.96 seconds to recover.
>
> Jenkins, GitLab, Cloud Run/Monitoring, rollback, and ServiceNow assets are implemented, but I label them pending until executed in authenticated environments rather than presenting configuration as production evidence.

## Demonstration order

1. CI badge and verified results.
2. Health, readiness, metrics, and status endpoints.
3. PowerShell monitor and deduplication logic.
4. RCA timeline.
5. Jenkins gates and rollback.
6. Evidence map and limitations.

