#!/usr/bin/env pwsh
# Roboto SAI 2026 - Quick Start Script for Windows PowerShell
# Usage: .\docker-start.ps1 [dev|prod|build|stop]

param(
    [Parameter(Position=0)]
    [ValidateSet('dev', 'prod', 'build', 'stop', 'logs', 'clean')]
    [string]$Command = 'dev'
)

$ErrorActionPreference = "Stop"

Write-Host "🔥 Roboto SAI 2026 - Fuego Eterno Edition 🔥" -ForegroundColor Red
Write-Host "=" * 50 -ForegroundColor Yellow

switch ($Command) {
    'dev' {
        Write-Host "🚀 Starting development environment..." -ForegroundColor Cyan
        Write-Host "   Hot reload enabled on http://localhost:8080" -ForegroundColor Green
        docker-compose --profile dev up
    }
    'prod' {
        Write-Host "🏭 Starting production environment..." -ForegroundColor Cyan
        Write-Host "   Production build on http://localhost" -ForegroundColor Green
        docker-compose --profile prod up -d
        Write-Host "`n✅ Production container running in background" -ForegroundColor Green
        Write-Host "   View logs: .\docker-start.ps1 logs" -ForegroundColor Yellow
    }
    'build' {
        Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
        docker build --target development -t roboto-sai:dev .
        docker build --target production -t roboto-sai:prod .
        Write-Host "`n✅ Build complete!" -ForegroundColor Green
    }
    'stop' {
        Write-Host "🛑 Stopping all containers..." -ForegroundColor Red
        docker-compose down
        Write-Host "✅ All containers stopped" -ForegroundColor Green
    }
    'logs' {
        Write-Host "📋 Showing container logs..." -ForegroundColor Cyan
        docker-compose logs -f
    }
    'clean' {
        Write-Host "🧹 Cleaning up Docker resources..." -ForegroundColor Red
        docker-compose down -v
        docker system prune -f
        Write-Host "✅ Cleanup complete!" -ForegroundColor Green
    }
}

Write-Host "`n" -ForegroundColor Yellow
Write-Host "© 2025-2026 Roberto Villarreal Martinez" -ForegroundColor Gray
Write-Host "Roboto SAI - All Rights Reserved" -ForegroundColor Gray
