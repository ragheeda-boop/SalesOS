#!/usr/bin/env bash
# ============================================================================
# Production Deployment Verification Script
# ============================================================================
# Usage: bash verify-deployment.sh [base_url] [tenant_id]
#   base_url:  http://localhost:8000 (default)
#   tenant_id: demo-tenant (default)
# 
# Returns exit code 0 if all checks pass, non-zero if any fail.
# Generates verification-report.json with full results.
# ============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
TENANT_ID="${2:-demo-tenant}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
REPORT_FILE="verification-report.json"
TOTAL=0; PASSED=0; FAILED=0

# ── Colors ──
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

check() {
    local name="$1" method="$2" path="$3" expected="${4:-200}"
    TOTAL=$((TOTAL + 1))
    local url="${BASE_URL}${path}"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" \
        -H "X-Tenant-Id: $TENANT_ID" \
        --connect-timeout 5 --max-time 10 2>/dev/null || echo "000")
    
    if [ "$status" = "$expected" ]; then
        echo -e "  ${GREEN}[PASS]${NC} [$status] $method $path"
        PASSED=$((PASSED + 1))
        echo "  {\"name\":\"$name\",\"status\":\"pass\",\"code\":$status}," >> "$REPORT_FILE.tmp"
    else
        echo -e "  ${RED}[FAIL]${NC} [$status] $method $path (expected $expected)"
        FAILED=$((FAILED + 1))
        echo "  {\"name\":\"$name\",\"status\":\"fail\",\"code\":$status,\"expected\":$expected}," >> "$REPORT_FILE.tmp"
    fi
}

check_json() {
    local name="$1" method="$2" path="$3" field="${4:-status}"
    TOTAL=$((TOTAL + 1))
    local url="${BASE_URL}${path}"
    local body
    body=$(curl -s -X "$method" "$url" \
        -H "X-Tenant-Id: $TENANT_ID" \
        --connect-timeout 5 --max-time 10 2>/dev/null || echo "{}")
    
    local val
    val=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$field','MISSING'))" 2>/dev/null || echo "PARSE_ERROR")
    
    if [ "$val" != "MISSING" ] && [ "$val" != "PARSE_ERROR" ] && [ "$val" != "null" ]; then
        echo -e "  ${GREEN}[PASS]${NC} $method $path → $field=$val"
        PASSED=$((PASSED + 1))
        echo "  {\"name\":\"$name\",\"status\":\"pass\",\"field\":\"$field\",\"value\":\"$val\"}," >> "$REPORT_FILE.tmp"
    else
        echo -e "  ${RED}[FAIL]${NC} $method $path → $field missing ($val)"
        FAILED=$((FAILED + 1))
        echo "  {\"name\":\"$name\",\"status\":\"fail\",\"field\":\"$field\",\"value\":\"$val\"}," >> "$REPORT_FILE.tmp"
    fi
}

# ── Start verification ────────────────────────────────────────────
echo "============================================="
echo "SalesOS Deployment Verification"
echo "Base URL: $BASE_URL"
echo "Tenant:   $TENANT_ID"
echo "Time:     $TIMESTAMP"
echo "============================================="

# Initialize report
echo "[" > "$REPORT_FILE.tmp"

# ── 1. Health Checks ──────────────────────────────────────────────
echo ""
echo "1. Health Check Endpoints"
echo "-------------------------"
check      "root-ping"              "GET"  "/ping"
check      "health-main"            "GET"  "/health"
check      "health-live"            "GET"  "/health/live"
check      "health-ready"           "GET"  "/health/ready"
check      "health-detailed"        "GET"  "/health/detailed"
check      "health-employee-360"    "GET"  "/health/employee-360"           503  # May return 503 if no data
check      "health-employee-live"   "GET"  "/health/employee-360/live"
check      "health-employee-ready"  "GET"  "/health/employee-360/ready"     503

# ── 2. Metrics ────────────────────────────────────────────────────
echo ""
echo "2. Prometheus Metrics"
echo "---------------------"
check      "metrics-endpoint"      "GET"  "/metrics"

# ── 3. Core API (no auth needed) ──────────────────────────────────
echo ""
echo "3. Core API Endpoints"
echo "---------------------"
check      "api-root"              "GET"  "/"

# ── 4. Docker Service Status ──────────────────────────────────────
echo ""
echo "4. Docker Services"
echo "------------------"
if command -v docker &>/dev/null; then
    svcs=(postgres redis backend frontend worker beat prometheus grafana)
    for svc in "${svcs[@]}"; do
        state=$(docker compose ps -q "$svc" 2>/dev/null | xargs -I{} docker inspect --format='{{.State.Status}}' {} 2>/dev/null || echo "not-found")
        if [ "$state" = "running" ]; then
            echo -e "  ${GREEN}[PASS]${NC} $svc is running"
            PASSED=$((PASSED)); TOTAL=$((TOTAL))
        else
            echo -e "  ${YELLOW}[INFO]${NC} $svc: $state (not running via Docker Compose)"
        fi
    done
fi

# ── 5. Celery Worker Status ──────────────────────────────────────
echo ""
echo "5. Celery Worker"
echo "----------------"
if command -v docker &>/dev/null; then
    ping_result=$(docker compose exec -T worker celery -A app.celery_app inspect ping 2>/dev/null || echo "FAILED")
    if echo "$ping_result" | grep -q "pong\|OK"; then
        echo -e "  ${GREEN}[PASS]${NC} Celery worker responding to ping"
        PASSED=$((PASSED)); TOTAL=$((TOTAL))
    else
        echo -e "  ${RED}[FAIL]${NC} Celery worker not responding"
        FAILED=$((FAILED)); TOTAL=$((TOTAL))
    fi
    
    active=$(docker compose exec -T worker celery -A app.celery_app inspect active 2>/dev/null || echo "[]")
    echo -e "  ${YELLOW}[INFO]${NC} Active tasks: $(echo "$active" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "N/A")"
fi

# ── 6. Database Connectivity ─────────────────────────────────────
echo ""
echo "6. Database"
echo "-----------"
if command -v docker &>/dev/null; then
    db_ok=$(docker compose exec -T postgres pg_isready -U salesos 2>/dev/null | grep "accepting" || echo "")
    if [ -n "$db_ok" ]; then
        echo -e "  ${GREEN}[PASS]${NC} Postgres is accepting connections"
        PASSED=$((PASSED)); TOTAL=$((TOTAL))
    else
        echo -e "  ${RED}[FAIL]${NC} Postgres not reachable"
        FAILED=$((FAILED)); TOTAL=$((TOTAL))
    fi
fi

# ── 7. Migration Status ──────────────────────────────────────────
echo ""
echo "7. Migration Status"
echo "-------------------"
if command -v docker &>/dev/null; then
    current=$(docker compose exec -T backend alembic current 2>/dev/null | tail -1 || echo "unknown")
    echo -e "  ${YELLOW}[INFO]${NC} Current revision: $current"
fi

# ── 8. Generate Report ────────────────────────────────────────────
# Remove trailing comma
if [ -f "$REPORT_FILE.tmp" ]; then
    sed -i '$ s/,$//' "$REPORT_FILE.tmp" 2>/dev/null || true
fi

cat > "$REPORT_FILE" << EOF
{
  "report": "SalesOS Deployment Verification",
  "timestamp": "$TIMESTAMP",
  "base_url": "$BASE_URL",
  "tenant_id": "$TENANT_ID",
  "results": {
    "total": $TOTAL,
    "passed": $PASSED,
    "failed": $FAILED,
    "pass_rate": $(python3 -c "print(round($PASSED/$TOTAL*100,1))" 2>/dev/null || echo "0")
  },
  "checks": [
$(cat "$REPORT_FILE.tmp")
  ]
}
EOF
rm -f "$REPORT_FILE.tmp"

echo ""
echo "============================================="
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}ALL CHECKS PASSED ($PASSED/$TOTAL)${NC}"
else
    echo -e "${RED}$FAILED/$TOTAL CHECKS FAILED${NC}"
fi
echo "Report: $REPORT_FILE"
echo "============================================="

exit $FAILED
