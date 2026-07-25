# Probe Wave13 API residuals. Password from DEMO_ADMIN_PASSWORD / SMOKE_PASSWORD / seed default.
# Never prints password or token. Writes status codes only.
$ErrorActionPreference = "Continue"
$base = "http://127.0.0.1:8000"
$email = if ($env:SMOKE_EMAIL) { $env:SMOKE_EMAIL } else { "admin@salesos.io" }
$pass = if ($env:DEMO_ADMIN_PASSWORD) { $env:DEMO_ADMIN_PASSWORD }
  elseif ($env:SMOKE_PASSWORD) { $env:SMOKE_PASSWORD }
  else { "Admin@123!" }

$loginBody = @{ email = $email; password = $pass } | ConvertTo-Json
try {
  $login = Invoke-RestMethod -Uri "$base/api/v1/identity/login" -Method POST -Body $loginBody -ContentType "application/json" -TimeoutSec 30
} catch {
  Write-Output "LOGIN_FAIL"
  exit 2
}
$token = $login.access_token
if (-not $token) { $token = $login.accessToken }
$parts = $token.Split('.')
$pad = $parts[1] + ('=' * ((4 - ($parts[1].Length % 4)) % 4))
$payload = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($pad.Replace('-','+').Replace('_','/'))) | ConvertFrom-Json
$tenant = [string]$payload.tenant_id
Write-Output "LOGIN_OK tenant_present=$([bool]$tenant)"

$h = @{ Authorization = "Bearer $token"; "X-Tenant-Id" = $tenant }
$hAuth = @{ Authorization = "Bearer $token" }

$paths = @(
  "/api/v1/workflows",
  "/api/v1/workflows/analytics",
  "/api/v1/search/analytics?days=30",
  "/api/v1/copilot/telemetry?days=30",
  "/api/v1/pipeline/analytics",
  "/api/v1/revenue/dashboard",
  "/api/v1/forecast",
  "/api/v1/workspace",
  "/api/v1/employees?limit=100",
  "/api/v1/analytics/kpis"
)

$results = @()
foreach ($path in $paths) {
  try {
    $resp = Invoke-WebRequest -Uri ($base + $path) -Headers $h -Method GET -TimeoutSec 60 -UseBasicParsing
    $code = [int]$resp.StatusCode
    $snippet = ""
  } catch {
    $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { -1 }
    try {
      $reader = [IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
      $snippet = ($reader.ReadToEnd()).Substring(0, [Math]::Min(180, $_.Exception.Response.ContentLength))
    } catch { $snippet = "" }
  }
  Write-Output ("{0} -> {1}" -f $path, $code)
  if ($snippet) { Write-Output ("  detail: {0}" -f $snippet) }
  $results += [pscustomobject]@{ path = $path; status = $code }
}

# no-tenant-header regression
foreach ($path in @("/api/v1/pipeline/analytics","/api/v1/revenue/dashboard")) {
  try {
    $resp = Invoke-WebRequest -Uri ($base + $path) -Headers $hAuth -Method GET -TimeoutSec 60 -UseBasicParsing
    $code = [int]$resp.StatusCode
  } catch {
    $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { -1 }
  }
  Write-Output ("{0} (auth-only) -> {1}" -f $path, $code)
  $results += [pscustomobject]@{ path = "$path#auth-only"; status = $code }
}

foreach ($origin in @("http://localhost:3000","http://127.0.0.1:3000")) {
  try {
    $cors = Invoke-WebRequest -Uri "$base/api/v1/workspace" -Method OPTIONS -Headers @{
      Origin = $origin
      "Access-Control-Request-Method" = "GET"
      "Access-Control-Request-Headers" = "authorization,content-type,x-tenant-id,accept"
    } -TimeoutSec 15 -UseBasicParsing
    $acao = $cors.Headers["Access-Control-Allow-Origin"]
    Write-Output ("CORS {0} -> {1} acao={2}" -f $origin, [int]$cors.StatusCode, $acao)
    $results += [pscustomobject]@{ path = "cors:$origin"; status = [int]$cors.StatusCode }
  } catch {
    $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { -1 }
    Write-Output ("CORS {0} -> {1}" -f $origin, $code)
    $results += [pscustomobject]@{ path = "cors:$origin"; status = $code }
  }
}

try {
  $oa = Invoke-RestMethod -Uri "$base/openapi.json" -TimeoutSec 30
  $names = @($oa.paths.PSObject.Properties.Name | Where-Object { $_ -match "forecast|workspace|pipeline/analytics|revenue/dashboard|workflows/analytics|search/analytics|copilot/telemetry$" })
  Write-Output "OPENAPI:"
  $names | ForEach-Object { Write-Output $_ }
} catch {
  Write-Output "OPENAPI_FAIL"
}

$outDir = Join-Path $PSScriptRoot "..\docs\audit\ga-engineering-audit\evidence\wave13-api-residual-fix"
# When run from salesos/, adjust:
if (-not (Test-Path $outDir)) {
  $outDir = "C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide\docs\audit\ga-engineering-audit\evidence\wave13-api-residual-fix"
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmmssZ")
$results | ConvertTo-Json | Set-Content (Join-Path $outDir "probe-$stamp.json") -Encoding utf8
Write-Output "WROTE probe-$stamp.json"
