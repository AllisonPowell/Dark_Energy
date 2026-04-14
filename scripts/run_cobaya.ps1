param(
    [Parameter(Mandatory=$true)]
    [string]$RunFile
)

$ErrorActionPreference = "Stop"

$RunFilePath = Resolve-Path $RunFile

Write-Host ""
Write-Host "========================================="
Write-Host " Running Cobaya"
Write-Host "========================================="
Write-Host "Config file: $RunFilePath"
Write-Host ""

if (-not (Test-Path $RunFilePath)) {
    Write-Error "YAML file not found: $RunFilePath"
    exit 1
}

$LogDir = "outputs\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$BaseName = [System.IO.Path]::GetFileNameWithoutExtension($RunFilePath)
$TimeStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "$BaseName`_$TimeStamp.log"

Write-Host "Log file: $LogFile"
Write-Host ""

try {
    $cobayaCmd = Get-Command cobaya-run -ErrorAction SilentlyContinue

    if ($null -ne $cobayaCmd) {
        cobaya-run $RunFilePath 2>&1 | Tee-Object -FilePath $LogFile
    }
    else {
        # Fallback: suppress the known harmless warning
        $env:PYTHONWARNINGS = "ignore:'cobaya.run' found in sys.modules:RuntimeWarning"
        python -W ignore::RuntimeWarning -m cobaya.run $RunFilePath 2>&1 | Tee-Object -FilePath $LogFile
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Cobaya exited with code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "Run completed successfully"
}
catch {
    Write-Host ""
    Write-Error "Cobaya run failed: $($_.Exception.Message)"
    exit 1
}