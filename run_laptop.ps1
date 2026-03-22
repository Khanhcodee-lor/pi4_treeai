$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

if (-not $env:FIREBASE_KEY_PATH) {
    $defaultKeyPath = Join-Path $projectRoot "firebase_key.json"
    $env:FIREBASE_KEY_PATH = $defaultKeyPath
}

if (-not $env:CAMERA_BACKEND) {
    $env:CAMERA_BACKEND = "opencv"
}

if (-not $env:CAMERA_INDEX) {
    $env:CAMERA_INDEX = "0"
}

if (-not $env:DEVICE_ID) {
    $env:DEVICE_ID = "tomato_001"
}

if (-not $env:DEVICE_ROOT) {
    $env:DEVICE_ROOT = "plants"
}

Write-Host "Starting Tree AI in laptop mode..."
Write-Host "Project root: $projectRoot"
Write-Host "Firebase key: $env:FIREBASE_KEY_PATH"
Write-Host "Camera backend: $env:CAMERA_BACKEND"
Write-Host "Camera index: $env:CAMERA_INDEX"
Write-Host "Device id: $env:DEVICE_ID"
Write-Host "Device root: $env:DEVICE_ROOT"

if (-not (Test-Path $env:FIREBASE_KEY_PATH)) {
    Write-Error "Firebase key not found. Put firebase_key.json in $projectRoot or set FIREBASE_KEY_PATH before running."
}

python -m src.main
