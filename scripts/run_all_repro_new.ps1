$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Full pipeline: both chains + plots"
Write-Host "========================================="
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot



$PantheonYaml = Join-Path $ProjectRoot "runs\linear_potential_bao_pantheon_sh0es_repro.yaml"
$Desy5Yaml    = Join-Path $ProjectRoot "runs\linear_potential_bao_desy5.yaml"

$PantheonRoot = Join-Path $ProjectRoot "outputs\linear_potential_bao_pantheon_sh0es_repro"
$Desy5Root    = Join-Path $ProjectRoot "outputs\linear_potential_bao_desy5"


$PlotsDir     = Join-Path $ProjectRoot "outputs\plots"
$LogsDir      = Join-Path $ProjectRoot "outputs\logs"

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
    Invoke-CobayaYaml -YamlPath $PantheonYaml -Label "pantheon"
    Invoke-CobayaYaml -YamlPath $Desy5Yaml -Label "desy5"

    Write-Host ""
    Write-Host "==> Generating plots"
    Write-Host ""

    python (Join-Path $ProjectRoot "scripts\make_plots.py") `
        --pantheon-root $PantheonRoot `
        --desy5-root $Desy5Root `
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
    Write-Host "  $PantheonRoot"
    Write-Host "  $Desy5Root"
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