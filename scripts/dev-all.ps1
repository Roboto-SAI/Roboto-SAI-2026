#!/usr/bin/env pwsh
# Roboto SAI Development Environment Setup
# Start all services locally (without Docker)

param(
    [switch]$Stop
)

if ($Stop) {
    Write-Host "🛑 Stopping Roboto SAI Development Environment" -ForegroundColor Red
    Get-Process -Name "node", "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ All services stopped" -ForegroundColor Green
    exit
}

Write-Host "🚀 Starting Roboto SAI Development Environment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Function to start process in background
function Start-BackgroundProcess {
    param($Name, $Command, $WorkingDirectory)

    Write-Host "Starting $Name..." -ForegroundColor Yellow
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "pwsh.exe"
    $startInfo.Arguments = "-Command `"$Command`""
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $true
    $startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $process.Start() | Out-Null

    return $process
}

# Start backend (Python)
$backendProcess = Start-BackgroundProcess "Backend API Server" "python main_modular.py" "$PSScriptRoot\..\backend"

# Wait for backend to start
Start-Sleep -Seconds 5

# Start OS Agent (Node.js)
$osAgentProcess = Start-BackgroundProcess "OS Agent (MCP Host)" "npm run dev" "$PSScriptRoot\..\os-agent"

# Wait for OS Agent to start
Start-Sleep -Seconds 3

# Build MCP servers
Write-Host "Building MCP servers..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\mcp-servers\fs-server"
npm run build
Pop-Location

# Start MCP filesystem server
$fsServerProcess = Start-BackgroundProcess "MCP Filesystem Server" "npm start" "$PSScriptRoot\..\mcp-servers\fs-server"

# Start frontend (Vite)
$frontendProcess = Start-BackgroundProcess "Frontend Dev Server" "npm run dev" "$PSScriptRoot\.."

Write-Host "" -ForegroundColor Green
Write-Host "✅ All services starting..." -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "🔗 Service URLs:" -ForegroundColor Cyan
Write-Host "   Frontend:    http://localhost:8080" -ForegroundColor White
Write-Host "   Backend:     http://localhost:5000" -ForegroundColor White
Write-Host "   OS Agent:    http://localhost:5055" -ForegroundColor White
Write-Host "   MCP FS:      Running in background" -ForegroundColor White
Write-Host "" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow

# Wait for user interrupt
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "" -ForegroundColor Red
    Write-Host "🛑 Stopping all services..." -ForegroundColor Red
    Get-Process -Name "node", "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ All services stopped" -ForegroundColor Green
}