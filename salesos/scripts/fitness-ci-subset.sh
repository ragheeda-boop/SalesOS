#!/usr/bin/env bash
# Fitness CI subset — FF-07 / FF-09 / FF-10 / FF-12 (EAB-001-P2-FIT-01)
# Light shell/grep checks only — not full test suites.
# Plan: docs/audit/ga-engineering-audit/FITNESS-CI-SUBSET-PLAN.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
FAIL=0

pass() { echo "[PASS] $*"; }
fail() { echo "[FAIL] $*"; FAIL=1; }

echo "=== Fitness CI subset (FF-07/AIGOV, FF-DUP-01, FF-09, FF-10, FF-12) ==="
echo "ROOT=$ROOT"

# ── FF-07: feature_ai_copilot default False + FE STUB honesty ─────────────
echo ""
echo "--- FF-07 AI honesty ---"
if rg -n "feature_ai_copilot:\s*bool\s*=\s*False" salesos/backend/app/config.py >/dev/null; then
  pass "FF-07: feature_ai_copilot defaults False in config.py"
else
  fail "FF-07: feature_ai_copilot must default to False in config.py"
fi

if rg -n "STUB" salesos/frontend/packages/platform/decision/index.ts >/dev/null \
  && rg -n "STUB|not implemented|not production" -i salesos/frontend/packages/platform/decision/README.md >/dev/null; then
  pass "FF-07: FE decision package STUB labeled (code + README)"
else
  fail "FF-07: FE decision STUB marker missing"
fi

if rg -n "0\.0\.0-stub|STUB" salesos/frontend/packages/platform/decision/package.json >/dev/null; then
  pass "FF-07: FE decision package.json STUB/version marker"
else
  fail "FF-07: FE decision package.json missing 0.0.0-stub / STUB"
fi

if rg -n '"name":\s*"@salesos/decision-platform-lab"' salesos/packages/platform/decision/package.json >/dev/null \
  && rg -n "TWIN|lab|NOT the FE" -i salesos/packages/platform/decision/package.json >/dev/null; then
  pass "FF-07: lab twin renamed to @salesos/decision-platform-lab"
else
  fail "FF-07: lab twin must be @salesos/decision-platform-lab (not colliding FE name)"
fi

# Light FF-14: product src must not call stub decisionEngine.evaluate/explain
if rg -n "decisionEngine\.(evaluate|explain)" salesos/frontend/src --glob "*.{ts,tsx}" >/dev/null 2>&1; then
  fail "FF-07/FF-14: product path must not call stub decisionEngine.evaluate/explain"
else
  pass "FF-07/FF-14: no stub decisionEngine.evaluate/explain in frontend/src"
fi

if [[ -f docs/audit/ga-engineering-audit/AI_HONESTY.md ]]; then
  pass "FF-07: AI_HONESTY.md present"
else
  fail "FF-07: AI_HONESTY.md missing"
fi

# Light AIGOV: Arabic detect/prompts + telemetry/log must reference the gate
COPILOT=salesos/backend/app/routers/copilot.py
if rg -n "require_ai_copilot_enabled" "$COPILOT" >/dev/null \
  && rg -n -U '(?s)arabic/detect.{0,400}require_ai_copilot_enabled' "$COPILOT" >/dev/null \
  && rg -n -U '(?s)arabic/prompts.{0,500}require_ai_copilot_enabled' "$COPILOT" >/dev/null \
  && rg -n -U '(?s)telemetry/log.{0,500}require_ai_copilot_enabled' "$COPILOT" >/dev/null; then
  pass "FF-07/AIGOV: arabic detect/prompts + telemetry/log gated"
else
  fail "FF-07/AIGOV: arabic detect/prompts + telemetry/log must Depends(require_ai_copilot_enabled)"
fi
if rg -n 'deprecated\s*=\s*True' salesos/backend/app/routers/ai.py >/dev/null \
  && rg -n '/ai/generate' salesos/backend/app/routers/ai.py >/dev/null \
  && rg -n '/ai/evaluate' salesos/backend/app/routers/ai.py >/dev/null; then
  pass "FF-07/AIGOV: /ai/generate|/ai/evaluate OpenAPI-deprecated"
else
  fail "FF-07/AIGOV: /ai/generate|/ai/evaluate must remain OpenAPI-deprecated"
fi

# ── FF-DUP-01 (light): Decision HTTP SoT remount posture ───────────────────
echo ""
echo "--- FF-DUP-01 Decision SoT remount ---"
SOT_DOC="docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-001/DECISION-API-SOT.md"
if [[ -f "$SOT_DOC" ]]; then
  pass "FF-DUP-01: DECISION-API-SOT.md present"
else
  fail "FF-DUP-01: DECISION-API-SOT.md missing"
fi
if rg -n 'prefix="/api/v1/decision-runtime"' salesos/backend/app/boot/routers.py >/dev/null \
  && rg -n 'Decision Center \(SoT\)' salesos/backend/app/boot/routers.py >/dev/null \
  && rg -n 'decision-runtime' salesos/backend/runtime/decision_runtime/router.py >/dev/null; then
  pass "FF-DUP-01: Runtime remount prefix + Center SoT tag + router docstring"
else
  fail "FF-DUP-01: Decision Runtime remount / Center SoT markers missing"
fi
# Tight positive: decision_router include uses decision-runtime (not bare /api/v1)
if rg -n -U '(?s)include_router\(\s*decision_router,\s*prefix="/api/v1/decision-runtime"' \
  salesos/backend/app/boot/routers.py >/dev/null; then
  pass "FF-DUP-01: decision_router include is /api/v1/decision-runtime only"
else
  fail "FF-DUP-01: decision_router must include at prefix=/api/v1/decision-runtime"
fi
# FE /decisions ledger: Center feedback only — no Runtime accept/dismiss hybrid
DECISIONS_PAGE="salesos/frontend/src/app/(dashboard)/decisions/page.tsx"
if [[ -f "$DECISIONS_PAGE" ]] \
  && ! rg -n 'decision-runtime' "$DECISIONS_PAGE" >/dev/null \
  && rg -n '/api/v1/decisions/\$\{id\}/feedback' "$DECISIONS_PAGE" >/dev/null; then
  pass "FF-DUP-01: FE /decisions uses Center feedback; no decision-runtime"
else
  fail "FF-DUP-01: FE /decisions must use Center /feedback and not call decision-runtime"
fi
# Platform explain must stay tenant-scoped (signature guard)
if rg -n 'def explain\(self, decision_id: str, tenant_id: str\)' \
  salesos/backend/app/modules/decision/engine.py >/dev/null \
  && rg -n 'engine\.explain\(decision_id, tenant_id\)' \
  salesos/backend/app/modules/decision/router.py >/dev/null; then
  pass "FF-DUP-01: Platform explain is tenant-scoped"
else
  fail "FF-DUP-01: Platform explain must take and pass tenant_id"
fi

# ── FF-DUP-02 (light): search + prompt dual-registry quarantine ────────────
echo ""
echo "--- FF-DUP-02 search/prompt quarantine ---"
SEARCH_PY=salesos/backend/app/routers/search.py
if rg -n '/search/analytics' "$SEARCH_PY" >/dev/null \
  && rg -n '/search/semantic' "$SEARCH_PY" >/dev/null \
  && rg -n '/search/similar' "$SEARCH_PY" >/dev/null \
  && [[ "$(rg -c 'deprecated\s*=\s*True' "$SEARCH_PY" | awk -F: '{s+=$2} END {print s+0}')" -ge 3 ]]; then
  pass "FF-DUP-02: search experimental routes OpenAPI-deprecated"
else
  fail "FF-DUP-02: search analytics/semantic/similar must stay OpenAPI-deprecated"
fi
if rg -n 'prompt dual-registry' salesos/backend/app/modules/tenant_studio/prompt_library_router.py >/dev/null; then
  pass "FF-DUP-02: Studio prompt dual-registry tag present"
else
  fail "FF-DUP-02: Studio prompt dual-registry OpenAPI tag missing"
fi

# ── FF-09: dual compose SoT doc + MetaData() ceiling ──────────────────────
echo ""
echo "--- FF-09 compose / MetaData ---"
if [[ -f docs/ops/COMPOSE-SOURCE-OF-TRUTH.md ]]; then
  pass "FF-09: COMPOSE-SOURCE-OF-TRUTH.md present"
else
  fail "FF-09: COMPOSE-SOURCE-OF-TRUTH.md missing"
fi

if [[ -f docs/audit/ga-engineering-audit/METADATA-ISLAND-FREEZE.md ]]; then
  pass "FF-09: METADATA-ISLAND-FREEZE.md present"
else
  fail "FF-09: METADATA-ISLAND-FREEZE.md missing"
fi

# Ceiling: EAB-003 19→18 (MCP); 2026-08-12 18→17 (pgvector); 2026-08-12b 17→13 (benchmark+admin table()); 2026-08-13 13→6 (query/DML stubs table()).
MD_COUNT=$(rg -c "MetaData\(" salesos/backend --glob "*.py" | awk -F: '{s+=$2} END {print s+0}')
MD_CEILING=6
if [[ "$MD_COUNT" -le "$MD_CEILING" ]]; then
  pass "FF-09: MetaData() count=$MD_COUNT <= ceiling=$MD_CEILING"
else
  fail "FF-09: MetaData() count=$MD_COUNT exceeds ceiling=$MD_CEILING (update freeze + DEC if intentional)"
fi

# ── FF-10: middleware fail-closed if db_session_factory unset (grep posture) ─
echo ""
echo "--- FF-10 middleware fail-closed posture ---"
# Entitlement / suspended / API-key middleware must reference factory and fail closed (503), not skip.
for hint in "db_session_factory" "503"; do
  if rg -n "$hint" salesos/backend/app/modules/admin/entitlement_middleware.py \
       salesos/backend/app/modules/identity/suspended_tenant_middleware.py \
       salesos/backend/app/modules/api_keys/middleware.py >/dev/null; then
    :
  else
    fail "FF-10: expected '$hint' in entitlement/suspended/api_keys middleware"
  fi
done
# Wire assignment present in boot startup
if rg -n "db_session_factory\s*=" salesos/backend/app/boot/startup.py >/dev/null; then
  pass "FF-10: db_session_factory wired in boot/startup.py; middleware files reference factory + 503"
else
  fail "FF-10: db_session_factory assignment missing in boot/startup.py"
fi

# ── FF-12: superseded GO docs must carry SUPERSEDED banner ────────────────
echo ""
echo "--- FF-12 superseded GO docs ---"
for doc in docs/vnext/reports/GO_NO_GO_DECISION.md docs/vnext/reports/GA_CHECKLIST.md; do
  if [[ -f "$doc" ]] && rg -n "SUPERSEDED" "$doc" >/dev/null; then
    pass "FF-12: $doc has SUPERSEDED banner"
  elif [[ ! -f "$doc" ]]; then
    pass "FF-12: $doc absent (ok)"
  else
    fail "FF-12: $doc missing SUPERSEDED banner"
  fi
done

echo ""
if [[ "$FAIL" -ne 0 ]]; then
  echo "Fitness CI subset FAILED"
  exit 1
fi
echo "Fitness CI subset PASSED (light validated — not full FF catalog / not Production GO)"
exit 0
