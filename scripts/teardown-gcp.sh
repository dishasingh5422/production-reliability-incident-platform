#!/usr/bin/env bash
set -euo pipefail

PROJECT=""
REGION="asia-south1"
SERVICE="production-reliability-platform"
REPOSITORY="reliability-images"
CONFIRM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --confirm) CONFIRM="$2"; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if [[ -z "$PROJECT" || "$CONFIRM" != "$SERVICE" ]]; then
  printf 'Refusing teardown. Use: %s --project PROJECT_ID --confirm %s\n' "$0" "$SERVICE" >&2
  exit 2
fi

gcloud config set project "$PROJECT" >/dev/null
gcloud run services delete "$SERVICE" --region "$REGION" --quiet
gcloud artifacts repositories delete "$REPOSITORY" --location "$REGION" --quiet
printf 'Removed Cloud Run service %s and Artifact Registry repository %s from project %s.\n' \
  "$SERVICE" "$REPOSITORY" "$PROJECT"

