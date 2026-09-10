#!/usr/bin/env bash
set -euo pipefail

PROJECT=""
REGION="asia-south1"
SERVICE="production-reliability-platform"
REVISION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --revision) REVISION="$2"; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if [[ -z "$PROJECT" || -z "$REVISION" ]]; then
  printf 'Usage: %s --project PROJECT_ID --revision REVISION [--region REGION]\n' "$0" >&2
  exit 2
fi

gcloud config set project "$PROJECT" >/dev/null
gcloud run services update-traffic "$SERVICE" \
  --region "$REGION" \
  --to-revisions "${REVISION}=100"

SERVICE_URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
curl --silent --show-error --fail "$SERVICE_URL/healthz" | jq -e '.status == "healthy"' >/dev/null
printf 'Rollback verified: %s now serves 100%% of traffic.\n' "$REVISION"

