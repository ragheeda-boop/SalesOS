# Fitness CI subset - FF-07 / FF-09 / FF-10 / FF-12 (EAB-001-P2-FIT-01)
# Light grep checks only - Windows host twin of fitness-ci-subset.sh
# Plan: docs/audit/ga-engineering-audit/FITNESS-CI-SUBSET-PLAN.md
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$Fail = 0

function Pass([string]$Msg) { Write-Host "[PASS] $Msg" }
function Fail([string]$Msg) { Write-Host "[FAIL] $Msg"; $script:Fail = 1 }

function Find-Rg {
  $cmd = Get-Command rg -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cursorRg = Join-Path $env:LOCALAPPDATA "Programs\cursor\resources\app\node_modules\@vscode\ripgrep\bin\rg.exe"
  if (Test-Path $cursorRg) { return $cursorRg }
  return $null
}

Write-Host "=== Fitness CI subset (FF-07/AIGOV, FF-DUP-01, FF-09, FF-10, FF-12) ==="
Write-Host "ROOT=$Root"

# FF-07
Write-Host ""
Write-Host "--- FF-07 AI honesty ---"
if (Select-String -Path "salesos\backend\app\config.py" -Pattern "feature_ai_copilot:\s*bool\s*=\s*False" -Quiet) {
  Pass "FF-07: feature_ai_copilot defaults False in config.py"
} else {
  Fail "FF-07: feature_ai_copilot must default to False in config.py"
}
$stubCode = Select-String -Path "salesos\frontend\packages\platform\decision\index.ts" -Pattern "STUB" -Quiet
$stubReadme = Select-String -Path "salesos\frontend\packages\platform\decision\README.md" -Pattern "STUB|not implemented|not production" -Quiet
if ($stubCode -and $stubReadme) {
  Pass "FF-07: FE decision package STUB labeled (code + README)"
} else {
  Fail "FF-07: FE decision STUB marker missing"
}
$stubPkg = Select-String -Path "salesos\frontend\packages\platform\decision\package.json" -Pattern "0\.0\.0-stub|STUB" -Quiet
if ($stubPkg) {
  Pass "FF-07: FE decision package.json STUB/version marker"
} else {
  Fail "FF-07: FE decision package.json missing 0.0.0-stub / STUB"
}
$labName = Select-String -Path "salesos\packages\platform\decision\package.json" -Pattern '"name":\s*"@salesos/decision-platform-lab"' -Quiet
$labDesc = Select-String -Path "salesos\packages\platform\decision\package.json" -Pattern "TWIN|lab|NOT the FE" -Quiet
if ($labName -and $labDesc) {
  Pass "FF-07: lab twin renamed to @salesos/decision-platform-lab"
} else {
  Fail "FF-07: lab twin must be @salesos/decision-platform-lab (not colliding FE name)"
}
$stubHits = Get-ChildItem -Path "salesos\frontend\src" -Recurse -Include *.ts,*.tsx -File -ErrorAction SilentlyContinue |
  Select-String -Pattern "decisionEngine\.(evaluate|explain)"
if ($null -ne $stubHits -and @($stubHits).Count -gt 0) {
  Fail "FF-07/FF-14: product path must not call stub decisionEngine.evaluate/explain"
} else {
  Pass "FF-07/FF-14: no stub decisionEngine.evaluate/explain in frontend/src"
}
if (Test-Path "docs\audit\ga-engineering-audit\AI_HONESTY.md") {
  Pass "FF-07: AI_HONESTY.md present"
} else {
  Fail "FF-07: AI_HONESTY.md missing"
}
$copilot = Get-Content "salesos\backend\app\routers\copilot.py" -Raw
if (
  $copilot -match "require_ai_copilot_enabled" -and
  $copilot -match "(?s)arabic/detect.{0,400}require_ai_copilot_enabled" -and
  $copilot -match "(?s)arabic/prompts.{0,500}require_ai_copilot_enabled" -and
  $copilot -match "(?s)telemetry/log.{0,500}require_ai_copilot_enabled"
) {
  Pass "FF-07/AIGOV: arabic detect/prompts + telemetry/log gated"
} else {
  Fail "FF-07/AIGOV: arabic detect/prompts + telemetry/log must Depends(require_ai_copilot_enabled)"
}
$aiRouter = Get-Content "salesos\backend\app\routers\ai.py" -Raw
if (
  $aiRouter -match 'deprecated\s*=\s*True' -and
  $aiRouter -match '/ai/generate' -and
  $aiRouter -match '/ai/evaluate'
) {
  Pass "FF-07/AIGOV: /ai/generate|/ai/evaluate OpenAPI-deprecated"
} else {
  Fail "FF-07/AIGOV: /ai/generate|/ai/evaluate must remain OpenAPI-deprecated"
}

# FF-DUP-01
Write-Host ""
Write-Host "--- FF-DUP-01 Decision SoT remount ---"
$sotDoc = "docs\audit\ga-engineering-audit\enterprise-audit-board\history\EAB-2026-08-06-001\DECISION-API-SOT.md"
if (Test-Path $sotDoc) {
  Pass "FF-DUP-01: DECISION-API-SOT.md present"
} else {
  Fail "FF-DUP-01: DECISION-API-SOT.md missing"
}
$boot = Get-Content "salesos\backend\app\boot\routers.py" -Raw
$rtDoc = Get-Content "salesos\backend\runtime\decision_runtime\router.py" -Raw
if (
  $boot -match 'prefix="/api/v1/decision-runtime"' -and
  $boot -match 'Decision Center \(SoT\)' -and
  $rtDoc -match "decision-runtime"
) {
  Pass "FF-DUP-01: Runtime remount prefix + Center SoT tag + router docstring"
} else {
  Fail "FF-DUP-01: Decision Runtime remount / Center SoT markers missing"
}
# Tight block: only the decision_router include line group (avoid next router's /api/v1)
if ($boot -match '(?s)include_router\(\s*decision_router,\s*prefix="/api/v1/decision-runtime"') {
  Pass "FF-DUP-01: decision_router include is /api/v1/decision-runtime only"
} else {
  Fail "FF-DUP-01: decision_router must include at prefix=/api/v1/decision-runtime"
}

# FF-DUP-02 (light)
Write-Host ""
Write-Host "--- FF-DUP-02 search/prompt quarantine ---"
$search = Get-Content "salesos\backend\app\routers\search.py" -Raw
$depCount = ([regex]::Matches($search, 'deprecated\s*=\s*True')).Count
if (
  $search -match '/search/analytics' -and
  $search -match '/search/semantic' -and
  $search -match '/search/similar' -and
  $depCount -ge 3
) {
  Pass "FF-DUP-02: search experimental routes OpenAPI-deprecated"
} else {
  Fail "FF-DUP-02: search analytics/semantic/similar must stay OpenAPI-deprecated"
}
if (Select-String -Path "salesos\backend\app\modules\tenant_studio\prompt_library_router.py" -Pattern "prompt dual-registry" -Quiet) {
  Pass "FF-DUP-02: Studio prompt dual-registry tag present"
} else {
  Fail "FF-DUP-02: Studio prompt dual-registry OpenAPI tag missing"
}

# FF-09
Write-Host ""
Write-Host "--- FF-09 compose / MetaData ---"
if (Test-Path "docs\ops\COMPOSE-SOURCE-OF-TRUTH.md") {
  Pass "FF-09: COMPOSE-SOURCE-OF-TRUTH.md present"
} else {
  Fail "FF-09: COMPOSE-SOURCE-OF-TRUTH.md missing"
}
if (Test-Path "docs\audit\ga-engineering-audit\METADATA-ISLAND-FREEZE.md") {
  Pass "FF-09: METADATA-ISLAND-FREEZE.md present"
} else {
  Fail "FF-09: METADATA-ISLAND-FREEZE.md missing"
}
$mdCeiling = 18
$rg = Find-Rg
if ($rg) {
  $mdOut = & $rg -c --glob "*.py" "MetaData\(" "salesos\backend" 2>$null
  $mdMatches = 0
  foreach ($line in $mdOut) {
    if ($line -match ":(\d+)$") { $mdMatches += [int]$Matches[1] }
  }
} else {
  $mdMatches = (
    Get-ChildItem -Path "salesos\backend" -Recurse -Filter "*.py" -File |
      Where-Object { $_.FullName -notmatch "\\__pycache__\\|\\\.venv\\|\\venv\\" } |
      Select-String -Pattern "MetaData\(" |
      Measure-Object
  ).Count
}
if ($mdMatches -le $mdCeiling) {
  Pass "FF-09: MetaData() count=$mdMatches <= ceiling=$mdCeiling"
} else {
  Fail "FF-09: MetaData() count=$mdMatches exceeds ceiling=$mdCeiling"
}

# FF-10
Write-Host ""
Write-Host "--- FF-10 middleware fail-closed posture ---"
$mw = @(
  "salesos\backend\app\modules\admin\entitlement_middleware.py",
  "salesos\backend\app\modules\identity\suspended_tenant_middleware.py",
  "salesos\backend\app\modules\api_keys\middleware.py"
)
$okFactory = $true
$ok503 = $true
foreach ($f in $mw) {
  if (-not (Select-String -Path $f -Pattern "db_session_factory" -Quiet)) { $okFactory = $false }
  if (-not (Select-String -Path $f -Pattern "503" -Quiet)) { $ok503 = $false }
}
$wired = Select-String -Path "salesos\backend\app\boot\startup.py" -Pattern "db_session_factory\s*=" -Quiet
if ($okFactory -and $ok503 -and $wired) {
  Pass "FF-10: db_session_factory wired; middleware files reference factory + 503"
} else {
  Fail "FF-10: fail-closed posture markers missing"
}

# FF-12
Write-Host ""
Write-Host "--- FF-12 superseded GO docs ---"
foreach ($doc in @(
  "docs\vnext\reports\GO_NO_GO_DECISION.md",
  "docs\vnext\reports\GA_CHECKLIST.md"
)) {
  if (-not (Test-Path $doc)) {
    Pass "FF-12: $doc absent (ok)"
  } elseif (Select-String -Path $doc -Pattern "SUPERSEDED" -Quiet) {
    Pass "FF-12: $doc has SUPERSEDED banner"
  } else {
    Fail "FF-12: $doc missing SUPERSEDED banner"
  }
}

Write-Host ""
if ($Fail -ne 0) {
  Write-Host "Fitness CI subset FAILED"
  exit 1
}
Write-Host "Fitness CI subset PASSED (light validated - not full FF catalog / not Production GO)"
exit 0
