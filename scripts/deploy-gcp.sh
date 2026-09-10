#!/usr/bin/env bash
set -euo pipefail

PROJECT=""
REGION="asia-south1"
COMMIT_SHA="$(git rev-parse HEAD 2>/dev/null || printf 'local')"
SERVICE="production-reliability-platform"
REPOSITORY="reliability-images"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --commit) COMMIT_SHA="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if [[ -z "$PROJECT" ]]; then
  printf 'Usage: %s --project PROJECT_ID [--region REGION] [--commit SHA]\n' "$0" >&2
  exit 2
fi

for command in gcloud docker jq; do
  command -v "$command" >/dev/null || {
    printf 'Required command not found: %s\n' "$command" >&2
    exit 1
  }
done

ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -1)"
if [[ -z "$ACCOUNT" ]]; then
  printf 'No active gcloud account. Authenticate before deployment.\n' >&2
  exit 1
fi

gcloud config set project "$PROJECT" >/dev/null
gcloud services enable run.googleapis.com artifactregistry.googleapis.com monitoring.googleapis.com

if ! gcloud artifacts repositories describe "$REPOSITORY" \
  --location "$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPOSITORY" \
    --repository-format docker \
    --location "$REGION" \
    --description "Production reliability portfolio images"
fi

REGISTRY="${REGION}-docker.pkg.dev"
IMAGE="${REGISTRY}/${PROJECT}/${REPOSITORY}/${SERVICE}:${COMMIT_SHA}"
gcloud auth configure-docker "$REGISTRY" --quiet

PREVIOUS_REVISION="$(gcloud run services describe "$SERVICE" \
  --region "$REGION" \
  --format='value(status.traffic[0].revisionName)' 2>/dev/null || true)"

docker build --platform linux/amd64 --tag "$IMAGE" .
docker push "$IMAGE"

gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --max-instances 2 \
  --min-instances 0 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "APP_ENV=gcp,APP_VERSION=${COMMIT_SHA},INCIDENT_PROVIDER=mock,ENABLE_FAULT_INJECTION=false"

SERVICE_URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
curl --silent --show-error --fail "$SERVICE_URL/healthz" | jq -e '.status == "healthy"' >/dev/null

mkdir -p evidence/runtime
jq -n \
  --arg project "$PROJECT" \
  --arg region "$REGION" \
  --arg service "$SERVICE" \
  --arg image "$IMAGE" \
  --arg url "$SERVICE_URL" \
  --arg commit_sha "$COMMIT_SHA" \
  --arg previous_revision "$PREVIOUS_REVISION" \
  '{project:$project,region:$region,service:$service,image:$image,url:$url,commit_sha:$commit_sha,previous_revision:$previous_revision,deployed_at:(now|todate)}' \
  > evidence/runtime/gcp-deployment.json

printf 'Cloud Run deployment verified at %s\n' "$SERVICE_URL"
printf 'Configure monitoring with: ./scripts/configure-gcp-monitoring.sh --project %s --url %s\n' \
  "$PROJECT" "$SERVICE_URL"

