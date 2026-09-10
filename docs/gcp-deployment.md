# Google Cloud deployment and monitoring

This integration is optional for the local MVP and must not be described as verified until the commands complete against the user's own project.

## Prerequisites

- Google Cloud project with billing enabled
- Active `gcloud` authentication
- Permission to enable APIs, create Artifact Registry repositories, deploy Cloud Run, and create Monitoring resources
- Docker and `jq`

## Deploy

```bash
./scripts/deploy-gcp.sh --project YOUR_PROJECT_ID --region asia-south1
```

The script enables only the required APIs, builds a Linux AMD64 image, pushes it to Artifact Registry, deploys a Cloud Run revision with a two-instance maximum, and verifies `/healthz`.

Cloud deployment uses the mock incident provider by default. Configure ServiceNow only after its credentials have been stored securely outside the repository.

## Configure monitoring

Use the verified service URL printed by the deployment script:

```bash
./scripts/configure-gcp-monitoring.sh \
  --project YOUR_PROJECT_ID \
  --url https://YOUR_CLOUD_RUN_HOST
```

This creates a one-minute HTTPS uptime check and an alert after sustained multi-region failures. Notification channels require separate user verification in the Google Cloud console.

## Roll back

Use the previous revision recorded in `evidence/runtime/gcp-deployment.json`:

```bash
./scripts/rollback-gcp.sh \
  --project YOUR_PROJECT_ID \
  --region asia-south1 \
  --revision PREVIOUS_REVISION
```

The rollback command routes all traffic to the selected revision and verifies `/healthz`.

## Teardown

The teardown command is deliberately guarded by an exact service-name confirmation:

```bash
./scripts/teardown-gcp.sh \
  --project YOUR_PROJECT_ID \
  --region asia-south1 \
  --confirm production-reliability-platform
```

It deletes only the named Cloud Run service and `reliability-images` Artifact Registry repository. Monitoring resources and the wider project are not deleted automatically.

