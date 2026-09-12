# Release and rollback

## Pre-deployment gates

1. Ruff, strict MyPy, and Bandit pass.
2. Pytest passes with at least 80% application coverage.
3. Compose configuration and Linux container build pass.
4. Container smoke test passes.
5. Monitoring/runbook impact and secret scan are reviewed.

## Deployment

Jenkins keeps `DEPLOY_TO_GCP=false` by default. Deployment requires an explicit project, region, and configured Jenkins file credential. The script records the previous revision, pushes a commit-tagged image, deploys, and verifies health.

## Rollback triggers

- Health or readiness failure after deployment.
- Sustained latency regression.
- New high-severity error signal.
- Failed smoke test.
- Security or data-integrity concern.

`scripts/rollback-gcp.sh` routes 100% of traffic to an explicitly named previous revision and verifies health. It never guesses the rollback target.

## Stakeholder update template

> Service: [name]  
> Impact: [synthetic impact]  
> Detected: [timestamp]  
> State: [investigating/recovering/resolved]  
> Evidence: [health/readiness/latency/log summary]  
> Action: [fix/rollback/recovery]  
> Next update: [time or closure condition]

