#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
ADMIN_TOKEN="${FAULT_ADMIN_TOKEN:-local-demo-token}"

json_post() {
  local endpoint="$1"
  local body="$2"
  curl --silent --show-error --fail \
    --request POST \
    --header 'content-type: application/json' \
    --data "$body" \
    "$BASE_URL$endpoint"
}

curl --silent --show-error --fail "$BASE_URL/healthz" | jq -e '.status == "healthy"' >/dev/null
curl --silent --show-error --fail "$BASE_URL/readyz" | jq -e '.status == "ready"' >/dev/null
curl --silent --show-error --fail "$BASE_URL/dashboard" | grep -q 'Reliability Control Room'
curl --silent --show-error --fail "$BASE_URL/metrics" | grep -q 'reliability_build_info'

failure_payload="{\"service_name\":\"production-reliability-platform\",\"check_type\":\"smoke-test\",\"target\":\"$BASE_URL\",\"healthy\":false,\"status_code\":503,\"diagnostic_summary\":\"controlled smoke-test failure\"}"
healthy_payload="{\"service_name\":\"production-reliability-platform\",\"check_type\":\"smoke-test\",\"target\":\"$BASE_URL\",\"healthy\":true,\"status_code\":200,\"diagnostic_summary\":\"recovery confirmed\"}"

created="$(json_post /api/checks "$failure_payload")"
incident_id="$(jq -r '.incident_id' <<<"$created")"
[[ "$(jq -r '.incident_action' <<<"$created")" == "created" ]]

json_post /api/checks "$failure_payload" | jq -e '.incident_action == "updated"' >/dev/null
json_post /api/checks "$healthy_payload" | jq -e '.incident_action == "recovery_pending"' >/dev/null
json_post /api/checks "$healthy_payload" | jq -e '.incident_action == "resolved"' >/dev/null
curl --silent --show-error --fail "$BASE_URL/api/incidents/$incident_id" |
  jq -e '.status == "RESOLVED" and .recovery_successes == 2' >/dev/null

unauthorised_status="$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --request POST "$BASE_URL/ops/faults/readiness")"
[[ "$unauthorised_status" == "401" ]]

curl --silent --show-error --fail \
  --request POST \
  --header "x-admin-token: $ADMIN_TOKEN" \
  "$BASE_URL/ops/faults/readiness" >/dev/null

failed_status="$(curl --silent --output /dev/null --write-out '%{http_code}' "$BASE_URL/readyz")"
[[ "$failed_status" == "503" ]]

curl --silent --show-error --fail \
  --request POST \
  --header "x-admin-token: $ADMIN_TOKEN" \
  "$BASE_URL/ops/recover" >/dev/null
curl --silent --show-error --fail "$BASE_URL/readyz" | jq -e '.status == "ready"' >/dev/null
curl --silent --show-error --fail "$BASE_URL/api/dashboard" |
  jq -e '.state == "operational" and (.recent_checks | length > 0)' >/dev/null

printf 'Smoke test passed: dashboard, monitoring, incident deduplication, recovery, and access controls.\n'
