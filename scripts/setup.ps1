$ErrorActionPreference = "Stop"

Write-Host "Setting up ULTRON CODE..."

python -m pip install --upgrade pip
python -m pip install -e ".[dev,api,automation,ocr]"

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host "Setup complete."
Write-Host "Run: ultron --help"
