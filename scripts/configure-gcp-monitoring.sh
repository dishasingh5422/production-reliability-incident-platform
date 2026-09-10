#!/usr/bin/env bash
set -euo pipefail

PROJECT=""
SERVICE_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --url) SERVICE_URL="$2"; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if [[ -z "$PROJECT" || -z "$SERVICE_URL" ]]; then
  printf 'Usage: %s --project PROJECT_ID --url https://SERVICE_URL\n' "$0" >&2
  exit 2
fi

for command in gcloud curl jq; do
  command -v "$command" >/dev/null || {
    printf 'Required command not found: %s\n' "$command" >&2
    exit 1
  }
done

HOSTNAME="$(python3 -c 'import sys,urllib.parse; print(urllib.parse.urlparse(sys.argv[1]).hostname)' "$SERVICE_URL")"
TOKEN="$(gcloud auth print-access-token)"
API="https://monitoring.googleapis.com/v3/projects/${PROJECT}"

uptime_payload="$(jq -n \
  --arg host "$HOSTNAME" \
  --arg project "$PROJECT" \
  '{displayName:"Production reliability health check",timeout:"10s",period:"60s",monitoredResource:{type:"uptime_url",labels:{host:$host,project_id:$project}},httpCheck:{path:"/healthz",port:443,useSsl:true,validateSsl:true,requestMethod:"GET"}}')"

uptime_response="$(curl --silent --show-error --fail \
  --request POST \
  --header "Authorization: Bearer $TOKEN" \
  --header 'Content-Type: application/json' \
  --data "$uptime_payload" \
  "$API/uptimeCheckConfigs")"
check_name="$(jq -r '.name' <<<"$uptime_response")"
check_id="${check_name##*/}"

alert_payload="$(jq -n \
  --arg check_id "$check_id" \
  '{displayName:"Production reliability uptime failure",combiner:"OR",enabled:true,documentation:{content:"Follow docs/operations-runbook.md. Validate health, readiness, DNS, TLS and database dependency before recovery or rollback.",mimeType:"text/markdown"},conditions:[{displayName:"Two-region uptime failure",conditionThreshold:{filter:("metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\""+$check_id+"\" AND resource.type=\"uptime_url\""),comparison:"COMPARISON_GT",thresholdValue:1,duration:"120s",aggregations:[{alignmentPeriod:"120s",perSeriesAligner:"ALIGN_NEXT_OLDER",crossSeriesReducer:"REDUCE_COUNT_FALSE",groupByFields:["resource.label.*"]}],trigger:{count:1}}}]}')"

alert_response="$(curl --silent --show-error --fail \
  --request POST \
  --header "Authorization: Bearer $TOKEN" \
  --header 'Content-Type: application/json' \
  --data "$alert_payload" \
  "$API/alertPolicies")"

mkdir -p evidence/runtime
jq -n \
  --arg uptime_check "$check_name" \
  --arg alert_policy "$(jq -r '.name' <<<"$alert_response")" \
  --arg hostname "$HOSTNAME" \
  '{uptime_check:$uptime_check,alert_policy:$alert_policy,hostname:$hostname,configured_at:(now|todate)}' \
  > evidence/runtime/gcp-monitoring.json

printf 'Created uptime check %s and alert policy %s\n' \
  "$check_name" "$(jq -r '.name' <<<"$alert_response")"
