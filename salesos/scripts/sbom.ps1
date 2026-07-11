param(
    [string]$OutputPath = (Join-Path $PSScriptRoot ".." "sbom.json")
)

function Write-Section {
    param($Header)
    Write-Host "`n==> $Header" -ForegroundColor Cyan
}

function Get-JsonSafe {
    param($Value)
    if ($null -eq $Value) { return $Value }
    try { return ($Value | ConvertTo-Json -Compress -Depth 10) } catch { return "null" }
}

$Sbom = @{
    bomFormat = "CycloneDX"
    specVersion = "1.5"
    version = 1
    metadata = @{
        timestamp = (Get-Date -Format "o")
        tools = @(
            @{ vendor = "SalesOS"; name = "sbom.ps1"; version = "1.0.0" }
        )
        component = @{
            type = "application"
            name = "salesos"
            version = "5.0.0"
        }
    }
    components = @()
    dependencies = @()
}

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")

# ── Frontend (npm/pnpm) ──
Write-Section "Frontend Dependencies"
$PackageJson = Join-Path $RootDir "frontend" "package.json"
if (Test-Path $PackageJson) {
    $Pkg = Get-Content $PackageJson -Raw | ConvertFrom-Json
    $AllDeps = @{}
    if ($Pkg.dependencies) { $Pkg.dependencies.PSObject.Properties | ForEach-Object { $AllDeps[$_.Name] = @{version = $_.Value; type = "runtime"} } }
    if ($Pkg.devDependencies) { $Pkg.devDependencies.PSObject.Properties | ForEach-Object { $AllDeps[$_.Name] = @{version = $_.Value; type = "dev"} } }

    foreach ($Dep in $AllDeps.GetEnumerator()) {
        $Name = $Dep.Key
        $Ver = $Dep.Value.version -replace '^\^|~|>=|<=|>|<', ''
        $Sbom.components += @{
            type = "library"
            name = $Name
            version = $Ver
            scope = if ($Dep.Value.type -eq "dev") { "optional" } else { "required" }
            "bom-ref" = $Name
            evidence = @{ identity = @{ field = "npm"; url = "https://www.npmjs.com/package/$Name" } }
        }
        $Sbom.dependencies += @{
            ref = $Name
            dependsOn = @()
        }
    }
    Write-Host "  Found $($AllDeps.Count) npm dependencies"
}

# ── Backend (Poetry / pip) ──
Write-Section "Backend Dependencies"
$Pyproject = Join-Path $RootDir "backend" "pyproject.toml"
if (Test-Path $Pyproject) {
    $Content = Get-Content $Pyproject -Raw
    $InDeps = $false
    $InDevDeps = $false
    $PyDeps = @{}
    foreach ($Line in $Content -split "`n") {
        $Trimmed = $Line.Trim()
        if ($Trimmed -eq "[tool.poetry.dependencies]") { $InDeps = $true; $InDevDeps = $false; continue }
        if ($Trimmed -eq "[tool.poetry.group.dev.dependencies]") { $InDeps = $false; $InDevDeps = $true; continue }
        if ($Trimmed -match "^\[") { $InDeps = $false; $InDevDeps = $false; continue }
        if (($InDeps -or $InDevDeps) -and $Trimmed -match '^([\w-]+)\s*=\s*"([^"]+)"') {
            $PkgName = $Matches[1]
            $PkgVer = $Matches[2]
            $PkgType = if ($InDevDeps) { "dev" } else { "runtime" }
            $PyDeps[$PkgName] = @{version = $PkgVer; type = $PkgType}
        }
    }

    foreach ($Dep in $PyDeps.GetEnumerator()) {
        $Name = $Dep.Key
        $Ver = $Dep.Value.version
        $Sbom.components += @{
            type = "library"
            name = $Name
            version = $Ver
            scope = if ($Dep.Value.type -eq "dev") { "optional" } else { "required" }
            "bom-ref" = "pypi:$Name"
            evidence = @{ identity = @{ field = "pypi"; url = "https://pypi.org/project/$Name" } }
        }
        $Sbom.dependencies += @{
            ref = "pypi:$Name"
            dependsOn = @()
        }
    }
    Write-Host "  Found $($PyDeps.Count) Python dependencies"
}

$SbomJson = $Sbom | ConvertTo-Json -Depth 10
$SbomJson | Out-File -FilePath $OutputPath -Encoding utf8
Write-Host "`nSBOM written to: $OutputPath" -ForegroundColor Green
Write-Host "Total components: $($Sbom.components.Count)" -ForegroundColor Green
