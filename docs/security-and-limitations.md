# Security and limitations

## Implemented safeguards

- Fault injection is disabled by default and requires a token.
- Secrets load from environment variables and log context is recursively redacted.
- Safe diagnostic codes replace connection-string output.
- The container runs as a non-root user.
- CI runs static security checks.
- GCP teardown requires an exact service-name confirmation.
- Runtime evidence is ignored until reviewed.

## Known limitations

- The Compose token is safe only for a local isolated drill.
- Fault state is process-local and unsuitable for multiple instances.
- Incident-list endpoints lack production authentication and RBAC.
- Cloud Run uses ephemeral SQLite unless external persistence is configured.
- ServiceNow uses developer-instance basic authentication; enterprise use should follow approved OAuth and governance.
- Jenkins controller, GitLab remote, GCP, Cloud Monitoring, and ServiceNow PDI remain pending.
- Geneos is not implemented.
- Local timings do not predict production SLA performance.

