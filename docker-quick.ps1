#!/usr/bin/env pwsh
# Docker Quick Start Script for Roboto SAI 2026

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'prod', 'build', 'down', 'logs', 'rebuild')]
    [string]$Action = 'dev'
)

$ErrorActionPreference = 'Stop'

Write-Host "?? Roboto SAI 2026 - Docker Manager" -ForegroundColor Cyan
Write-Host ""

switch ($Action) {
    'dev' {
        Write-Host "? Starting development environment..." -ForegroundColor Green
        docker compose --profile dev up -d
        Write-Host ""
        Write-Host "? Services started:" -ForegroundColor Green
        Write-Host "  - Frontend: http://localhost:8080" -ForegroundColor Yellow
        Write-Host "  - Backend API: http://localhost:5000" -ForegroundColor Yellow
        Write-Host "  - API Docs: http://localhost:5000/docs" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "? View logs with: .\docker-quick.ps1 logs" -ForegroundColor Cyan
    }
    'prod' {
        Write-Host "? Starting production environment..." -ForegroundColor Green
        docker compose --profile prod up -d
        Write-Host ""
        Write-Host "? Services started:" -ForegroundColor Green
        Write-Host "  - Frontend: http://localhost:80" -ForegroundColor Yellow
        Write-Host "  - Backend API: http://localhost:5000" -ForegroundColor Yellow
    }
    'build' {
        Write-Host "? Building Docker images..." -ForegroundColor Blue
        docker compose --profile dev build
        Write-Host "? Build complete!" -ForegroundColor Green
    }
    'rebuild' {
        Write-Host "? Rebuilding Docker images (no cache)..." -ForegroundColor Blue
        docker compose --profile dev build --no-cache
        Write-Host "? Rebuild complete!" -ForegroundColor Green
    }
    'down' {
        Write-Host "? Stopping all services..." -ForegroundColor Yellow
        docker compose --profile dev --profile prod down
        Write-Host "? All services stopped!" -ForegroundColor Green
    }
    'logs' {
        Write-Host "? Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
        docker compose --profile dev --profile prod logs -f
    }
}
