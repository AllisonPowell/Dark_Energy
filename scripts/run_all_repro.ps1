$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Full pipeline: chain + plots"
Write-Host "========================================="
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot



$ReproYaml = Join-Path $ProjectRoot "runs\linear_potential_bao_pantheon_sh0es_repro.yaml"

$ReproRoot = Join-Path $ProjectRoot "outputs\linear_potential_bao_pantheon_sh0es_repro"


$PlotsDir     = Join-Path $ProjectRoot "outputs\plots_repro"
$LogsDir      = Join-Path $ProjectRoot "outputs\logs_repro"

New-Item -ItemType Directory -Force -Path $PlotsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

function Invoke-CobayaYaml {
    param(
        [string]$YamlPath,
        [string]$Label
    )

    if (-not (Test-Path $YamlPath)) {
        throw "Missing YAML file: $YamlPath"
    }

    $TimeStamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $LogFile = Join-Path $LogsDir "$Label`_$TimeStamp.log"

    Write-Host ""
    Write-Host "==> Running chain: $Label"
    Write-Host "    YAML: $YamlPath"
    Write-Host "    Log : $LogFile"
    Write-Host ""

    $cobayaCmd = Get-Command cobaya-run -ErrorAction SilentlyContinue

    if ($null -ne $cobayaCmd) {
        cobaya-run $YamlPath 2>&1 | Tee-Object -FilePath $LogFile
    }
    else {
        $env:PYTHONWARNINGS = "ignore:'cobaya.run' found in sys.modules:RuntimeWarning"
        python -W ignore::RuntimeWarning -m cobaya.run $YamlPath 2>&1 | Tee-Object -FilePath $LogFile
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Cobaya chain '$Label' failed with exit code $LASTEXITCODE"
    }
}

try {
    Invoke-CobayaYaml -YamlPath $ReproYaml -Label "pantheon"


    Write-Host ""
    Write-Host "==> Generating plots"
    Write-Host ""

    python (Join-Path $ProjectRoot "scripts\make_plots_repro.py") `
        --repro-root $ReproRoot `
        --outdir $PlotsDir

    if ($LASTEXITCODE -ne 0) {
        throw "Plot generation failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "========================================="
    Write-Host " Pipeline completed successfully"
    Write-Host "========================================="
    Write-Host ""
    Write-Host "Chains:"
    Write-Host "  $ReproRoot"
    Write-Host ""
    Write-Host "Plots:"
    Write-Host "  $PlotsDir"
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Error "Pipeline failed: $($_.Exception.Message)"
    exit 1
}