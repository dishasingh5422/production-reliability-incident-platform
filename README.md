# Production Reliability & Incident Automation Platform

A portfolio-grade production-support simulation for monitoring a Python service, diagnosing application and dependency failures, managing incidents, validating deployments, and documenting recovery and root cause.

## Current status

Implementation is in progress. Only capabilities backed by successful tests or captured runtime evidence will be marked verified.

## Planned capabilities

- FastAPI health, readiness, status, metrics, and controlled fault endpoints
- PostgreSQL operational event, deployment, incident, and corrective-action records
- PowerShell HTTP, DNS, TLS, latency, and dependency monitoring
- Idempotent mock and ServiceNow incident adapters
- Jenkins pipeline and GitLab secondary CI workflow
- Google Cloud Run deployment and Cloud Monitoring configuration
- Controlled incident drill, runbook, RCA, and recruiter evidence pack

## Safety and limitations

- Synthetic operational data only
- No real bank, customer, or confidential data
- Fault injection is disabled by default and requires an admin token
- Credentials and local environment files must never be committed
- Live integrations are reported separately from local implementation

## Documentation

The architecture, local quickstart, operations runbook, release process, evidence, and verified results will be added as implementation milestones are completed.

