$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$DataDir = Join-Path $RootDir "data"

$DesiDir = Join-Path $DataDir "desi_dr2"
$PantheonDir = Join-Path $DataDir "pantheonplus"
$Desy5Dir = Join-Path $DataDir "desy5"
$CmbDir = Join-Path $DataDir "cmb_compressed"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
New-Item -ItemType Directory -Force -Path $DesiDir | Out-Null
New-Item -ItemType Directory -Force -Path $PantheonDir | Out-Null
New-Item -ItemType Directory -Force -Path $Desy5Dir | Out-Null
New-Item -ItemType Directory -Force -Path $CmbDir | Out-Null

function Checkout-RepoSparse {
    param(
        [string]$RepoUrl,
        [string]$TargetDir,
        [string[]]$SparsePaths
    )

    $GitDir = Join-Path $TargetDir ".git"

    if (-not (Test-Path $GitDir)) {
        git clone --filter=blob:none --no-checkout $RepoUrl $TargetDir
        git -C $TargetDir sparse-checkout init --cone
        git -C $TargetDir sparse-checkout set @SparsePaths

        try {
            git -C $TargetDir checkout main
        }
        catch {
            git -C $TargetDir checkout master
        }
    }
    else {
        git -C $TargetDir pull
    }
}

Write-Host "==> Downloading DESI DR2 BAO public data via CobayaSampler/bao_data"
$DesiRepoDir = Join-Path $DesiDir "bao_data"
Checkout-RepoSparse `
    -RepoUrl "https://github.com/CobayaSampler/bao_data.git" `
    -TargetDir $DesiRepoDir `
    -SparsePaths @("desi_bao_dr2", "README.md")

Write-Host "==> Downloading Pantheon+ data release subset"
$PantheonRepoDir = Join-Path $PantheonDir "DataRelease"
Checkout-RepoSparse `
    -RepoUrl "https://github.com/PantheonPlusSH0ES/DataRelease.git" `
    -TargetDir $PantheonRepoDir `
    -SparsePaths @("Pantheon+_Data/4_DISTANCES_AND_COVAR")

Write-Host "==> Downloading DES-SN5YR / DES-Dovekie SN distance products"
$Desy5RepoDir = Join-Path $Desy5Dir "DES-SN5YR"
Checkout-RepoSparse `
    -RepoUrl "https://github.com/des-science/DES-SN5YR.git" `
    -TargetDir $Desy5RepoDir `
    -SparsePaths @("4_DISTANCES_COVMAT")

Write-Host "==> Creating convenience copies/junction-like structure"

$PantheonCurrent = Join-Path $PantheonDir "current"
$PantheonSource = Join-Path $PantheonRepoDir "Pantheon+_Data\4_DISTANCES_AND_COVAR"

$Desy5Current = Join-Path $Desy5Dir "current"
$Desy5Source = Join-Path $Desy5RepoDir "4_DISTANCES_COVMAT"

if (Test-Path $PantheonCurrent) {
    Remove-Item $PantheonCurrent -Recurse -Force
}
if (Test-Path $Desy5Current) {
    Remove-Item $Desy5Current -Recurse -Force
}

# Try directory junction first; if that fails, fall back to copy
try {
    New-Item -ItemType Junction -Path $PantheonCurrent -Target $PantheonSource | Out-Null
}
catch {
    Copy-Item -Recurse -Force $PantheonSource $PantheonCurrent
}

try {
    New-Item -ItemType Junction -Path $Desy5Current -Target $Desy5Source | Out-Null
}
catch {
    Copy-Item -Recurse -Force $Desy5Source $Desy5Current
}

Write-Host ""
Write-Host "==> Data download complete"
Write-Host ""
Write-Host "DESI DR2 BAO folder:   $(Join-Path $DesiRepoDir 'desi_bao_dr2')"
Write-Host "Pantheon+ folder:      $PantheonCurrent"
Write-Host "DES-SN5YR folder:      $Desy5Current"
Write-Host ""
Write-Host "Reminder: place your compressed-CMB files under:"
Write-Host "  $CmbDir"
Write-Host ""
Write-Host "Typical DESY5 files expected by the likelihood:"
Write-Host "  DES-Dovekie_HD.csv"
Write-Host "  STAT+SYS.npz"
Write-Host "  STATONLY.npz"