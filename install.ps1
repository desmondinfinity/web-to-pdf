#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Step($msg) { Write-Host "`n── $msg ──" -ForegroundColor Cyan }

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  Web to PDF — Windows Installer" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# ── Python check ───────────────────────────────────────────────────────────────
Step "Checking Python"
try {
    $pyVer = & python --version 2>&1
    Write-Host "Found: $pyVer"
} catch {
    Write-Error "Python 3 is required. Install from https://www.python.org (check 'Add to PATH')."
    exit 1
}

# ── Python packages ────────────────────────────────────────────────────────────
Step "Installing Python packages"
python -m pip install --quiet PyQt6 playwright

# ── Playwright browser ─────────────────────────────────────────────────────────
Step "Installing Playwright browser"
python -m playwright install chromium

# ── Poppler (pdfunite) ─────────────────────────────────────────────────────────
Step "Installing poppler (pdfunite)"
$BinDir   = Join-Path $ScriptDir "bin"
$PdfUnite = Join-Path $BinDir "pdfunite.exe"

if (Test-Path $PdfUnite) {
    Write-Host "pdfunite already present, skipping download."
} else {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

    Write-Host "Fetching latest poppler release info..."
    $Release = Invoke-RestMethod "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"
    $Asset   = $Release.assets | Where-Object { $_.name -match "\.zip$" } | Select-Object -First 1
    if (-not $Asset) { Write-Error "Could not find poppler zip in release assets."; exit 1 }

    $ZipPath    = Join-Path $env:TEMP "poppler.zip"
    $ExtractDir = Join-Path $env:TEMP "poppler-extract"

    Write-Host "Downloading $($Asset.name)..."
    Invoke-WebRequest -Uri $Asset.browser_download_url -OutFile $ZipPath

    Write-Host "Extracting..."
    if (Test-Path $ExtractDir) { Remove-Item $ExtractDir -Recurse -Force }
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

    $PopplerBin = Get-ChildItem -Path $ExtractDir -Filter "bin" -Recurse -Directory |
                  Select-Object -First 1
    if (-not $PopplerBin) { Write-Error "bin/ folder not found in poppler archive."; exit 1 }

    Copy-Item -Path "$($PopplerBin.FullName)\*" -Destination $BinDir -Force
    Remove-Item $ZipPath, $ExtractDir -Recurse -Force
    Write-Host "pdfunite installed to .\bin\"
}

Write-Host "`n===================================" -ForegroundColor Green
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "  Run the app: launch.bat" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
