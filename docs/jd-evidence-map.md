# NatWest Production Analyst evidence map

Target: NatWest Production Analyst, Chennai, R-00281423. This is an independent portfolio simulation and does not imply access to NatWest systems.

| Role concept | Evidence | Status |
|---|---|---|
| Production/application support | Health/readiness, status, runbook, drill | Verified locally |
| Deployment quality | Ruff, MyPy, Bandit, 16 tests, 93% coverage, container smoke | Verified locally and in GitHub CI |
| Robustness and resilience | Readiness separation, recovery threshold, deduplication, rollback | Verified locally |
| CI/CD | GitHub CI, Jenkinsfile, GitLab pipeline | GitHub verified; Jenkins/GitLab runtime pending |
| SQL and Python | FastAPI/SQLAlchemy, PostgreSQL, schema and analytical SQL | Verified locally |
| PowerShell automation | DNS, HTTP, TLS, latency, readiness and incidents | Verified in PowerShell container |
| GCP | Cloud Run, Artifact Registry, Monitoring and rollback scripts | Implemented; live pending |
| Monitoring/support | Prometheus metrics, synthetic monitor, structured logs | Verified locally |
| Geneos | No implementation | Not claimed |
| Networking | DNS, ports, HTTP, TLS expiry, response codes | DNS/HTTP verified; live TLS pending |
| Incident management | Create, deduplicate, update, recover, resolve and RCA | Mock lifecycle verified |
| ServiceNow | Tested Table API adapter | Live PDI pending |
| Jenkins/GitHub/GitLab | GitHub history and CI plus pipeline-as-code | GitHub verified; others pending |

