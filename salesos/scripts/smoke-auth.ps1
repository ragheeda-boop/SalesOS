<#
.SYNOPSIS
  Wave 13 precursor - authenticated API smoke for SalesOS local Docker.

.DESCRIPTION
  Registers a disposable local user (or logs in with -Email/-Password),
  obtains a JWT, and probes critical paths. Never prints tokens.
  Does not weaken auth. Local-only disposable credentials by default.

.EXAMPLE
  .\scripts\smoke-auth.ps1
  .\scripts\smoke-auth.ps1 -BaseUrl http://localhost:8000 -FrontendUrl http://localhost:3000
  # Existing account via env (do not commit secrets):
  $env:SMOKE_EMAIL='…'; $env:SMOKE_PASSWORD='…'; .\scripts\smoke-auth.ps1 -SkipRegister
#>

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [string]$Email = "",
    [string]$Password = "SmokeAuthPass123!",
    [switch]$SkipFrontend,
    [switch]$SkipRegister
)

$ErrorActionPreference = "Stop"
$script:Results = New-Object System.Collections.Generic.List[object]
$script:Token = $null
$script:TenantId = $null

# Prefer process env over defaults (never hardcode demo/prod secrets in repo).
if (-not $Email -and $env:SMOKE_EMAIL) { $Email = $env:SMOKE_EMAIL }
if ($env:SMOKE_PASSWORD) { $Password = $env:SMOKE_PASSWORD }

if (-not $Email) {
    $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
    $Email = "smoke.w13.$suffix@example.com"
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("salesos-smoke-auth-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

function Write-Utf8NoBom {
    param([string]$Path, [string]$Value)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Value, $utf8)
}

function Write-Row {
    param([string]$Name, [string]$Expected, [int]$Actual, [bool]$Ok, [string]$Detail = "")
    $status = if ($Ok) { "PASS" } else { "FAIL" }
    $script:Results.Add([pscustomobject]@{
        Name     = $Name
        Expected = $Expected
        Actual   = $Actual
        Status   = $status
        Detail   = $Detail
    }) | Out-Null
    $color = if ($Ok) { "Green" } else { "Red" }
    $extra = if ($Detail) { " - $Detail" } else { "" }
    Write-Host ("  [{0}] {1} (expected {2}, got {3}){4}" -f $status, $Name, $Expected, $Actual, $extra) -ForegroundColor $color
}

function Invoke-Curl {
    param(
        [Parameter(Mandatory = $true)][string[]]$CurlArgs
    )
    $outFile = Join-Path $tmp ("body-" + [guid]::NewGuid().ToString("N") + ".txt")
    $allArgs = @("-sS", "--max-time", "60", "-o", $outFile, "-w", "%{http_code}") + $CurlArgs
    $codeRaw = & curl.exe @allArgs 2>&1
    if ($LASTEXITCODE -ne 0 -and -not ("$codeRaw" -match '^\d{3}$')) {
        $body = ""
        if (Test-Path $outFile) {
            $body = [System.IO.File]::ReadAllText($outFile)
        }
        return @{ Code = 0; Body = ("$codeRaw $body") }
    }
    $code = 0
    $raw = ("$codeRaw").Trim()
    if ($raw -match '(\d{3})$') { $code = [int]$Matches[1] }
    $body = ""
    if (Test-Path $outFile) {
        $body = [System.IO.File]::ReadAllText($outFile)
    }
    return @{ Code = $code; Body = $body }
}

function Get-JsonProp {
    param([string]$Json, [string]$Name)
    if (-not $Json) { return $null }
    try {
        $obj = $Json | ConvertFrom-Json
        return $obj.$Name
    } catch {
        return $null
    }
}

try {
    $acctLabel = if ($SkipRegister) { "existing (SkipRegister / SMOKE_* env)" } else { "disposable local" }
    Write-Host "========== SalesOS Auth Smoke (Wave 13 precursor) ==========" -ForegroundColor Cyan
    Write-Host "BaseUrl:     $BaseUrl"
    Write-Host "FrontendUrl: $FrontendUrl"
    Write-Host "Email:       $Email ($acctLabel)"
    Write-Host ""

    # NOTE: RateLimitMiddleware keys by IP only; identity tier is 10/min.
    # Do identity + CSRF early so the shared counter does not starve /identity/*.

    Write-Host "--- Auth gate (401 / CSRF reject) ---" -ForegroundColor Yellow

    $r = Invoke-Curl @(($BaseUrl + "/api/v1/companies"))
    Write-Row "GET /api/v1/companies (no token)" "401" $r.Code ($r.Code -eq 401)

    $r = Invoke-Curl @(($BaseUrl + "/api/v1/decisions"))
    Write-Row "GET /api/v1/decisions (no token)" "401" $r.Code ($r.Code -eq 401)

    $gqlPath = Join-Path $tmp "gql.json"
    Write-Utf8NoBom -Path $gqlPath -Value '{"query":"{ __typename }"}'
    $r = Invoke-Curl @(
        "-X", "POST", ($BaseUrl + "/graphql"),
        "-H", "Content-Type: application/json",
        "--data-binary", ("@" + $gqlPath)
    )
    Write-Row "POST /graphql (no CSRF)" "403" $r.Code ($r.Code -eq 403) "csrf_enforced"

    Write-Host ""
    Write-Host "--- Identity (register / login / csrf) ---" -ForegroundColor Yellow

    $tokenPresent = $false

    if (-not $SkipRegister) {
        $regPath = Join-Path $tmp "register.json"
        $regObj = @{ email = $Email; password = $Password; full_name = "Wave13 Smoke" } | ConvertTo-Json -Compress
        Write-Utf8NoBom -Path $regPath -Value $regObj

        $r = Invoke-Curl @(
            "-X", "POST", ($BaseUrl + "/api/v1/identity/register"),
            "-H", "Content-Type: application/json",
            "--data-binary", ("@" + $regPath)
        )
        if ($r.Code -in 200, 201) {
            $script:Token = Get-JsonProp $r.Body "access_token"
            $script:TenantId = [string](Get-JsonProp $r.Body "tenant_id")
            $tokenPresent = [bool]$script:Token
        }
        if ($r.Code -eq 429) {
            Write-Row "POST /api/v1/identity/register" "201" $r.Code $false "rate_limited_retry_after_60s"
            throw "Identity rate limited (429). Wait ~60s and re-run. Shared per-IP counter + identity tier=10."
        }
        Write-Row "POST /api/v1/identity/register" "201" $r.Code (($r.Code -in 200, 201) -and $tokenPresent) ("token_present=" + $tokenPresent)
    } else {
        Write-Host "  [SKIP] register (-SkipRegister / SMOKE_* env)" -ForegroundColor Yellow
    }

    $loginPath = Join-Path $tmp "login.json"
    $loginObj = @{ email = $Email; password = $Password } | ConvertTo-Json -Compress
    Write-Utf8NoBom -Path $loginPath -Value $loginObj

    $r = Invoke-Curl @(
        "-X", "POST", ($BaseUrl + "/api/v1/identity/login"),
        "-H", "Content-Type: application/json",
        "--data-binary", ("@" + $loginPath)
    )
    if ($r.Code -eq 200) {
        $t = Get-JsonProp $r.Body "access_token"
        $tid = Get-JsonProp $r.Body "tenant_id"
        if ($t) { $script:Token = $t; $tokenPresent = $true }
        if ($tid) { $script:TenantId = [string]$tid }
    }
    Write-Row "POST /api/v1/identity/login" "200" $r.Code (($r.Code -eq 200) -and $tokenPresent) ("token_present=" + $tokenPresent)

    if (-not $tokenPresent) {
        throw "No JWT obtained - cannot continue authenticated probes"
    }

    $authArgs = @(
        "-H", ("Authorization: Bearer " + $script:Token),
        "-H", ("X-Tenant-Id: " + $script:TenantId)
    )

    $jar = Join-Path $tmp "cookies.txt"
    $r = Invoke-Curl @("-c", $jar, "-b", $jar, ($BaseUrl + "/api/v1/identity/csrf-token"))
    $csrf = Get-JsonProp $r.Body "csrf_token"
    Write-Row "GET /api/v1/identity/csrf-token" "200" $r.Code (($r.Code -eq 200) -and [bool]$csrf) ("csrf_present=" + [bool]$csrf)

    Write-Host ""
    Write-Host "--- Authenticated ---" -ForegroundColor Yellow

    $r = Invoke-Curl (@(($BaseUrl + "/api/v1/identity/users/me")) + $authArgs)
    $meDetail = ""
    if ($r.Code -eq 200 -and $r.Body) {
        $role = Get-JsonProp $r.Body "role"
        if ($role) { $meDetail = "role=$role" }
    }
    Write-Row "GET /api/v1/identity/users/me" "200" $r.Code ($r.Code -eq 200) $meDetail

    $r = Invoke-Curl (@(($BaseUrl + "/api/v1/dashboard")) + $authArgs)
    Write-Row "GET /api/v1/dashboard (auth)" "200" $r.Code ($r.Code -eq 200)

    $r = Invoke-Curl (@(($BaseUrl + "/api/v1/companies")) + $authArgs)
    $detail = ""
    if ($r.Body) {
        try {
            $cj = $r.Body | ConvertFrom-Json
            if ($cj -is [System.Array]) { $detail = "items=$($cj.Count)" }
            elseif ($null -ne $cj.items) { $detail = "items=$($cj.items.Count)" }
            elseif ($null -ne $cj.data) { $detail = "items=$($cj.data.Count)" }
            elseif ($null -ne $cj.total) { $detail = "total=$($cj.total)" }
            else { $detail = "json_ok" }
        } catch {
            $detail = "parse_err"
        }
    }
    Write-Row "GET /api/v1/companies (auth)" "200" $r.Code ($r.Code -eq 200) $detail

    $r = Invoke-Curl (@(($BaseUrl + "/api/v1/decisions")) + $authArgs)
    Write-Row "GET /api/v1/decisions (auth)" "200" $r.Code ($r.Code -eq 200) ("bytes=" + $r.Body.Length)

    if ($csrf) {
        $gqlArgs = @(
            "-c", $jar, "-b", $jar,
            "-X", "POST", ($BaseUrl + "/graphql"),
            "-H", "Content-Type: application/json",
            "-H", ("X-CSRF-Token: " + $csrf)
        ) + $authArgs + @("--data-binary", ("@" + $gqlPath))
        $r = Invoke-Curl $gqlArgs
        $gqlOk = ($r.Code -eq 200) -and ($r.Body -match '__typename|Query|data')
        Write-Row "POST /graphql (auth+CSRF)" "200" $r.Code $gqlOk ("bytes=" + $r.Body.Length)
    } else {
        Write-Row "POST /graphql (auth+CSRF)" "200" 0 $false "skipped_no_csrf"
    }

    Write-Host ""
    Write-Host "--- Health / metrics / FE ---" -ForegroundColor Yellow

    $r = Invoke-Curl @(($BaseUrl + "/health"))
    Write-Row "GET /health" "200" $r.Code ($r.Code -eq 200)

    $r = Invoke-Curl @(($BaseUrl + "/metrics"))
    Write-Row "GET /metrics (unauth OK)" "200" $r.Code ($r.Code -eq 200) ("bytes=" + $r.Body.Length)

    if (-not $SkipFrontend) {
        $r = Invoke-Curl @(($FrontendUrl + "/"))
        Write-Row "GET frontend /" "200" $r.Code ($r.Code -eq 200)
    }
}
finally {
    $script:Token = $null
    $script:TenantId = $null
    if (Test-Path $tmp) {
        Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue
    }
}

$passN = @($script:Results | Where-Object { $_.Status -eq "PASS" }).Count
$failN = @($script:Results | Where-Object { $_.Status -eq "FAIL" }).Count
$total = $script:Results.Count

Write-Host ""
Write-Host "========== MATRIX ==========" -ForegroundColor Cyan
$script:Results | Format-Table -AutoSize
Write-Host ("PASS={0} FAIL={1} TOTAL={2}" -f $passN, $failN, $total)
if ($failN -gt 0) {
    Write-Host "OVERALL: FAIL" -ForegroundColor Red
    exit 1
}
Write-Host "OVERALL: PASS" -ForegroundColor Green
exit 0
