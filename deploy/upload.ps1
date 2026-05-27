# WeatherNext Pro — Upload to Vultr VM (run from your local Windows PC)
#
# Usage:
#   .\deploy\upload.ps1 -IP YOUR_VULTR_IP
#
# Prerequisites: ssh/scp must be available (built into Windows 10+)

param(
    [Parameter(Mandatory=$true)]
    [string]$IP,
    [string]$User = "root"
)

$ProjectDir = Split-Path -Parent $PSScriptRoot
$Remote = "${User}@${IP}"
$RemotePath = "/root/weathernext_pro"

Write-Host "=== Uploading WeatherNext Pro to ${Remote}:${RemotePath} ===" -ForegroundColor Cyan

# Files to upload (exclude .git, __pycache__, venv, logs)
$includes = @(
    "main.py",
    "resolve_signals.py",
    "score_signals.py",
    "check_signals.py",
    "find_markets.py",
    "inspect_markets.py",
    "requirements.txt",
    ".env",
    ".env.example",
    "config/config.yaml",
    "services/__init__.py",
    "services/weather_client.py",
    "services/market_scanner.py",
    "services/risk_manager.py",
    "services/scanner_runner.py",
    "deploy/setup_vultr.sh"
)

# Create remote directories
Write-Host "Creating remote directories..."
ssh ${Remote} "mkdir -p ${RemotePath}/config ${RemotePath}/services ${RemotePath}/deploy ${RemotePath}/data ${RemotePath}/logs"

# Upload each file
foreach ($file in $includes) {
    $localPath = Join-Path $ProjectDir $file
    if (Test-Path $localPath) {
        $remoteDest = "${Remote}:${RemotePath}/${file}"
        Write-Host "  Uploading $file..."
        scp $localPath $remoteDest
    } else {
        Write-Host "  SKIP (not found): $file" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Upload complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Now SSH in and run the setup script:"
Write-Host "  ssh ${Remote}"
Write-Host "  cd ${RemotePath}"
Write-Host "  bash deploy/setup_vultr.sh"
