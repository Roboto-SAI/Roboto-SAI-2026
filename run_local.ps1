# run_local.ps1
# Script to run Roboto SAI 2026 locally for testing

Write-Host "?? Starting Roboto SAI Local Development Environment..." -ForegroundColor Cyan

# Check for .venv
if (-not (Test-Path ".venv")) {
    Write-Host "? .venv not found at root. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
}

# Check for node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "? node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
}

# Load environment variables (optional, but good for visibility)
if (Test-Path ".env") {
    Write-Host "? .env file detected" -ForegroundColor Green
} else {
    Write-Host "?? .env file missing! Backend might fail." -ForegroundColor Red
}

Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host "Starting Backend on http://localhost:5000 (Proxy: http://localhost:5000/api)" -ForegroundColor Green
Write-Host "Starting Frontend on http://localhost:8080" -ForegroundColor Blue
Write-Host "Press Ctrl+C to stop both (Note: Backend may need manual stop if it persists)" -ForegroundColor Yellow
Write-Host "---------------------------------------------------" -ForegroundColor Gray

# Start Backend in a separate window to keep logs clean
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ..\.venv\Scripts\python.exe main.py" -WindowStyle Normal

# Start Frontend in current window
npm run dev
