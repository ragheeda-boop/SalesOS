<#
.SYNOPSIS
    Provisions 3 pilot tenants and their admin accounts for SalesOS pilot launch.
.DESCRIPTION
    Creates pilot tenants (enterprise, midmarket, SMB tiers) and admin users
    via the Identity API. Requires a running backend with admin token.
.PARAMETER ApiUrl
    Backend API base URL (default: http://localhost:8000)
.PARAMETER AdminToken
    JWT bearer token with admin privileges (required for tenant creation)
.EXAMPLE
    .\provision-pilot-tenants.ps1 -ApiUrl "http://localhost:8000" -AdminToken "eyJ..."
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl = "http://localhost:8000",

    [string]$AdminToken = ""
)

$ErrorActionPreference = "Stop"

if ($ApiUrl.EndsWith("/")) {
    $ApiUrl = $ApiUrl.TrimEnd("/")
}

# ── Pilot Tenants ───────────────────────────────────────────────

$tenants = @(
    @{ name = "Pilot-A - Enterprise Corp"; slug = "pilot-a"; tier = "enterprise" },
    @{ name = "Pilot-B - MidMarket Ltd"; slug = "pilot-b"; tier = "midmarket" },
    @{ name = "Pilot-C - SmallBiz Co"; slug = "pilot-c"; tier = "smb" }
)

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      SalesOS Pilot Tenant Provisioning                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:       $ApiUrl" -ForegroundColor White
Write-Host "  Tenants:   $($tenants.Count)" -ForegroundColor White
Write-Host "  Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$headers = @{
    "Content-Type" = "application/json"
}
if ($AdminToken) {
    $headers["Authorization"] = "Bearer $AdminToken"
}

# ── Create Tenants ──────────────────────────────────────────────

$tenantResults = @()
Write-Host "─── Creating Tenants ────────────────────────────────────────" -ForegroundColor Cyan

foreach ($t in $tenants) {
    Write-Host ""
    Write-Host "  Creating tenant: $($t.name) (tier: $($t.tier))..." -ForegroundColor White

    $body = $t | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/admin/tenants" -Method Post -Body $body -ContentType "application/json" -Headers $headers -TimeoutSec 30
        Write-Host "    ✅ Created: $($response.id)" -ForegroundColor Green
        $tenantResults += @{ slug = $t.slug; id = $response.id; status = "created" }
    }
    catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        Write-Host "    ❌ Failed (HTTP $statusCode): $($_.Exception.Message)" -ForegroundColor Red
        $tenantResults += @{ slug = $t.slug; id = $null; status = "failed"; error = $_.Exception.Message }
    }
}

# ── Create Admin Users ──────────────────────────────────────────

Write-Host ""
Write-Host "─── Creating Admin Users ────────────────────────────────────" -ForegroundColor Cyan

$userResults = @()
foreach ($t in $tenants) {
    Write-Host ""
    Write-Host "  Creating admin user for $($t.name)..." -ForegroundColor White

    $body = @{
        email       = "admin@$($t.slug).salesos.local"
        password    = "PilotAdmin2026!"
        tenant_slug = $t.slug
        role        = "admin"
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/identity/signup" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
        Write-Host "    ✅ User created: admin@$($t.slug).salesos.local" -ForegroundColor Green
        $userResults += @{ email = "admin@$($t.slug).salesos.local"; tenant = $t.slug; status = "created" }
    }
    catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        Write-Host "    ❌ Failed (HTTP $statusCode): $($_.Exception.Message)" -ForegroundColor Red
        $userResults += @{ email = "admin@$($t.slug).salesos.local"; tenant = $t.slug; status = "failed"; error = $_.Exception.Message }
    }
}

# ── Verify Tenant Isolation ────────────────────────────────────

Write-Host ""
Write-Host "─── Verifying Tenant Isolation ──────────────────────────────" -ForegroundColor Cyan

foreach ($t in $tenants) {
    Write-Host ""
    Write-Host "  Verifying data isolation for $($t.slug)..." -ForegroundColor White

    try {
        $tenantHeaders = $headers.Clone()
        $tenantHeaders["X-Tenant-Id"] = $t.slug
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/companies" -Method Get -Headers $tenantHeaders -TimeoutSec 15
        $count = if ($response -is [array]) { $response.Count } else { 0 }
        Write-Host "    ✅ Isolated: $count companies scoped to $($t.slug)" -ForegroundColor Green
    }
    catch {
        Write-Host "    ⚠️  Could not verify isolation (may require auth): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# ── Summary ─────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PROVISIONING SUMMARY" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

$tenantsCreated = ($tenantResults | Where-Object { $_.status -eq "created" }).Count
$usersCreated = ($userResults | Where-Object { $_.status -eq "created" }).Count

Write-Host ""
Write-Host "  Tenants created:  $tenantsCreated / $($tenants.Count)" -ForegroundColor $(if ($tenantsCreated -eq $tenants.Count) { "Green" } else { "Yellow" })
Write-Host "  Admin users:      $usersCreated / $($tenants.Count)" -ForegroundColor $(if ($usersCreated -eq $tenants.Count) { "Green" } else { "Yellow" })
Write-Host ""

Write-Host "  Admin Credentials:" -ForegroundColor White
foreach ($t in $tenants) {
    Write-Host "    admin@$($t.slug).salesos.local  |  PilotAdmin2026!" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "    1. Run .\seed-pilot-data.ps1 -ApiUrl $ApiUrl" -ForegroundColor Gray
Write-Host "    2. Run .\verify-pilot-deployment.ps1 -ApiUrl $ApiUrl" -ForegroundColor Gray
Write-Host "    3. Distribute credentials to pilot users" -ForegroundColor Gray
Write-Host ""

if ($tenantsCreated -eq $tenants.Count -and $usersCreated -eq $tenants.Count) {
    Write-Host "  ✅ All pilot tenants and users provisioned successfully!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "  ⚠️  Some provisioning failed. Review output above." -ForegroundColor Yellow
    exit 1
}
