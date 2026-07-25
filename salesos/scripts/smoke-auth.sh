#!/usr/bin/env bash
# Wave 13 precursor - authenticated API smoke for SalesOS local Docker.
# Never prints tokens. Local disposable credentials by default.
# Usage: bash salesos/scripts/smoke-auth.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
PASSWORD="${PASSWORD:-SmokeAuthPass123!}"
EMAIL="${EMAIL:-smoke.w13.$(date +%s)@example.com}"
SKIP_FRONTEND="${SKIP_FRONTEND:-0}"

PASS_N=0
FAIL_N=0
TMP="$(mktemp -d)"
TOKEN=""
TENANT=""
trap 'rm -rf "$TMP"; TOKEN=""; TENANT=""' EXIT

row() {
  local name="$1" expected="$2" actual="$3" ok="$4" detail="${5:-}"
  local status="FAIL"
  if [[ "$ok" == "1" ]]; then status="PASS"; PASS_N=$((PASS_N + 1)); else FAIL_N=$((FAIL_N + 1)); fi
  if [[ -n "$detail" ]]; then
    printf '  [%s] %s (expected %s, got %s) - %s\n' "$status" "$name" "$expected" "$actual" "$detail"
  else
    printf '  [%s] %s (expected %s, got %s)\n' "$status" "$name" "$expected" "$actual"
  fi
}

curl_code() {
  local out="$TMP/body.$$.$RANDOM.txt"
  local code
  code="$(curl -sS --max-time 60 -o "$out" -w '%{http_code}' "$@" || true)"
  BODY="$(cat "$out" 2>/dev/null || true)"
  CODE="$code"
}

json_prop() {
  # minimal extractor without jq dependency
  python3 - "$1" "$2" <<'PY' 2>/dev/null || true
import json,sys
try:
  obj=json.loads(sys.argv[1])
  v=obj.get(sys.argv[2])
  if v is None: raise SystemExit(0)
  print(v)
except Exception:
  pass
PY
}

echo "========== SalesOS Auth Smoke (Wave 13 precursor) =========="
echo "BaseUrl:     $BASE_URL"
echo "FrontendUrl: $FRONTEND_URL"
echo "Email:       $EMAIL (disposable local)"
echo

echo "--- Auth gate (401 / CSRF reject) ---"
curl_code "$BASE_URL/api/v1/companies"
[[ "$CODE" == "401" ]] && ok=1 || ok=0
row "GET /api/v1/companies (no token)" 401 "$CODE" "$ok"

curl_code "$BASE_URL/api/v1/decisions"
[[ "$CODE" == "401" ]] && ok=1 || ok=0
row "GET /api/v1/decisions (no token)" 401 "$CODE" "$ok"

printf '{"query":"{ __typename }"}' >"$TMP/gql.json"
curl_code -X POST "$BASE_URL/graphql" -H "Content-Type: application/json" --data-binary @"$TMP/gql.json"
[[ "$CODE" == "403" ]] && ok=1 || ok=0
row "POST /graphql (no CSRF)" 403 "$CODE" "$ok" "csrf_enforced"

echo
echo "--- Identity (register / login / csrf) ---"
printf '{"email":"%s","password":"%s","full_name":"Wave13 Smoke"}' "$EMAIL" "$PASSWORD" >"$TMP/reg.json"
curl_code -X POST "$BASE_URL/api/v1/identity/register" -H "Content-Type: application/json" --data-binary @"$TMP/reg.json"
TOKEN="$(json_prop "$BODY" access_token)"
TENANT="$(json_prop "$BODY" tenant_id)"
[[ "$CODE" =~ ^(200|201)$ && -n "$TOKEN" ]] && ok=1 || ok=0
row "POST /api/v1/identity/register" 201 "$CODE" "$ok" "token_present=$([[ -n $TOKEN ]] && echo True || echo False)"
if [[ "$CODE" == "429" ]]; then
  echo "Identity rate limited (429). Wait ~60s and re-run." >&2
  exit 1
fi

printf '{"email":"%s","password":"%s"}' "$EMAIL" "$PASSWORD" >"$TMP/login.json"
curl_code -X POST "$BASE_URL/api/v1/identity/login" -H "Content-Type: application/json" --data-binary @"$TMP/login.json"
t="$(json_prop "$BODY" access_token)"
tid="$(json_prop "$BODY" tenant_id)"
[[ -n "$t" ]] && TOKEN="$t"
[[ -n "$tid" ]] && TENANT="$tid"
[[ "$CODE" == "200" && -n "$TOKEN" ]] && ok=1 || ok=0
row "POST /api/v1/identity/login" 200 "$CODE" "$ok" "token_present=$([[ -n $TOKEN ]] && echo True || echo False)"

if [[ -z "$TOKEN" ]]; then
  echo "No JWT obtained - cannot continue" >&2
  exit 1
fi

AUTH=(-H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: $TENANT")
JAR="$TMP/cookies.txt"
curl_code -c "$JAR" -b "$JAR" "$BASE_URL/api/v1/identity/csrf-token"
CSRF="$(json_prop "$BODY" csrf_token)"
[[ "$CODE" == "200" && -n "$CSRF" ]] && ok=1 || ok=0
row "GET /api/v1/identity/csrf-token" 200 "$CODE" "$ok" "csrf_present=$([[ -n $CSRF ]] && echo True || echo False)"

echo
echo "--- Authenticated ---"
curl_code "${AUTH[@]}" "$BASE_URL/api/v1/identity/users/me"
[[ "$CODE" == "200" ]] && ok=1 || ok=0
row "GET /api/v1/identity/users/me" 200 "$CODE" "$ok"

curl_code "${AUTH[@]}" "$BASE_URL/api/v1/companies"
[[ "$CODE" == "200" ]] && ok=1 || ok=0
row "GET /api/v1/companies (auth)" 200 "$CODE" "$ok"

curl_code "${AUTH[@]}" "$BASE_URL/api/v1/decisions"
[[ "$CODE" == "200" ]] && ok=1 || ok=0
row "GET /api/v1/decisions (auth)" 200 "$CODE" "$ok"

if [[ -n "$CSRF" ]]; then
  curl_code -c "$JAR" -b "$JAR" -X POST "$BASE_URL/graphql" \
    -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
    "${AUTH[@]}" --data-binary @"$TMP/gql.json"
  if [[ "$CODE" == "200" && "$BODY" =~ (__typename|Query|data) ]]; then ok=1; else ok=0; fi
  row "POST /graphql (auth+CSRF)" 200 "$CODE" "$ok"
else
  row "POST /graphql (auth+CSRF)" 200 0 0 "skipped_no_csrf"
fi

echo
echo "--- Health / metrics / FE ---"
curl_code "$BASE_URL/health"
[[ "$CODE" == "200" ]] && ok=1 || ok=0
row "GET /health" 200 "$CODE" "$ok"

curl_code "$BASE_URL/metrics"
[[ "$CODE" == "200" ]] && ok=1 || ok=0
row "GET /metrics (unauth OK)" 200 "$CODE" "$ok"

if [[ "$SKIP_FRONTEND" != "1" ]]; then
  curl_code "$FRONTEND_URL/"
  [[ "$CODE" == "200" ]] && ok=1 || ok=0
  row "GET frontend /" 200 "$CODE" "$ok"
fi

echo
echo "========== MATRIX =========="
echo "PASS=$PASS_N FAIL=$FAIL_N TOTAL=$((PASS_N + FAIL_N))"
if [[ "$FAIL_N" -gt 0 ]]; then
  echo "OVERALL: FAIL"
  exit 1
fi
echo "OVERALL: PASS"
exit 0
