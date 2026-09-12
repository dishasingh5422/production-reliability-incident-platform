# Architecture and design decisions

## Reliability model

- `/healthz` answers whether the process is running without calling PostgreSQL.
- `/readyz` answers whether dependencies are available and the instance should receive traffic.

This avoids unnecessary process restart loops during a dependency outage while allowing a load balancer or deployment gate to remove an unready instance.

## Monitoring model

The PowerShell monitor collects DNS resolution, TCP/HTTPS reachability, TLS certificate lifetime, application liveness, database readiness, and response latency. It sends one normalized payload to the application, which assigns severity, stores evidence, and manages incidents.

## Incident model

An SHA-256 key derived from service, check type, and target identifies the active problem. Repeated failures update the open incident. Healthy observations increment a recovery counter; resolution occurs only after the configured threshold.

## Deployment model

GitHub is canonical and GitHub CI is verified. Jenkins is the release pipeline and keeps GCP deployment disabled by default. GitLab is an optional mirror. Cloud Run supplies managed HTTPS, revisions, scaling, and traffic routing without requiring Kubernetes.

## Key trade-offs

| Decision | Benefit | Limitation |
|---|---|---|
| Synchronous SQLAlchemy | Small and understandable support code | Lower concurrency than async persistence |
| Mock provider first | Fully testable without enterprise accounts | Not proof of ServiceNow execution |
| Process-local fault state | Safe, simple controlled drill | Does not coordinate across instances |
| SQLite default | Fast fresh-clone experience | Ephemeral on Cloud Run |
| PostgreSQL in Compose | Real SQL dependency and readiness behavior | Requires Docker |
| Prometheus endpoint | Portable metrics contract | No Geneos implementation |

