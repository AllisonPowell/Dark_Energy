$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Generate plots from existing chains"
Write-Host "========================================="
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$PantheonRoot = Join-Path $ProjectRoot "outputs\linear_potential_bao_pantheon_sh0es_repro"
$Desy5Root    = Join-Path $ProjectRoot "outputs\linear_potential_bao_desy5"

$PlotsDir     = Join-Path $ProjectRoot "outputs\bonus_plots"

New-Item -ItemType Directory -Force -Path $PlotsDir | Out-Null

if (-not (Test-Path ($PantheonRoot + ".1.txt"))) {
    throw "Missing Pantheon chain root files near: $PantheonRoot"
}

if (-not (Test-Path ($Desy5Root + ".1.txt"))) {
    throw "Missing DESY5 chain root files near: $Desy5Root"
}

try {
    Write-Host "==> Generating plots from existing chains"
    Write-Host "    Pantheon root: $PantheonRoot"
    Write-Host "    DESY5 root   : $Desy5Root"
    Write-Host "    Output dir   : $PlotsDir"
    Write-Host ""

    python (Join-Path $ProjectRoot "scripts\make_plots_from_chains.py") `
        --pantheon-root $PantheonRoot `
        --desy5-root $Desy5Root `
        --outdir $PlotsDir

    if ($LASTEXITCODE -ne 0) {
        throw "Plot generation failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "========================================="
    Write-Host " Plot generation completed successfully"
    Write-Host "========================================="
    Write-Host ""
    Write-Host "Plots:"
    Write-Host "  $PlotsDir"
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Error "Plot generation failed: $($_.Exception.Message)"
    exit 1
}