# Docker Container Fixes Applied

## Issues Identified and Fixed

### 1. Backend Dockerfile (backend/Dockerfile)
**Problem**: 
- Using Python 3.14 which doesn't exist (latest stable is 3.13)
- Incorrect file copy order causing build failures
- Health check using requests library which wasn't installed
- SDK installation conflicts with volume mounts

**Fixes Applied**:
- Changed base image from python:3.14-slim to python:3.13-slim
- Reordered COPY commands: SDK first, then requirements, then backend code
- Updated health check to use built-in urllib.request instead of requests
- Proper WORKDIR structure for better layer caching

### 2. Docker Compose (docker-compose.yml)
**Problem**:
- Conflicting volume mounts for the SDK (mounted as read-only but also needed for editable install)
- SDK mount was unnecessary since it's baked into the image

**Fixes Applied**:
- Removed the SDK volume mount (./workspaces/roboto-sai-sdk:/app/backend/sdk:ro)
- Kept only the backend code volume mount for hot-reload during development
- SDK is now properly installed in the image during build

### 3. Frontend Dockerfile (Dockerfile)
**Issues Fixed**:
- Removed reference to bun.lockb in COPY command (project uses npm)
- Added --legacy-peer-deps flag to handle dependency conflicts
- Added explicit --host 0.0.0.0 to dev server command for proper Docker networking
- Removed unnecessary Python from production nginx stage
- Fixed nginx config variable escaping

### 4. Additional Improvements
- Created docker-quick.ps1 PowerShell script for easier Docker management
- Verified .dockerignore is properly configured to exclude unnecessary files

## How to Use

### Start Development Environment
```powershell
# Using the quick script
.\docker-quick.ps1 dev

# Or manually
docker compose --profile dev up -d
```

### Build Images
```powershell
# Using the quick script
.\docker-quick.ps1 build

# Or manually
docker compose --profile dev build
```

### View Logs
```powershell
# Using the quick script
.\docker-quick.ps1 logs

# Or manually
docker compose logs -f
```

### Stop All Services
```powershell
# Using the quick script
.\docker-quick.ps1 down

# Or manually
docker compose --profile dev --profile prod down
```

## Services Overview

After starting with .\docker-quick.ps1 dev:

- **Frontend (Vite Dev Server)**: http://localhost:8080
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **API Health Check**: http://localhost:5000/api/health

## Network Architecture

- Frontend container: roboto-sai-dev
- Backend container: roboto-sai-backend
- Backend network: roboto-network (bridge driver)
- Frontend connects to backend via proxy configured in vite.config.ts

## Volume Mounts (Development)

- Frontend: Entire project directory mounted for hot-reload
- Backend: Only ./backend directory mounted for hot-reload
- Node modules: Anonymous volume to prevent host override

## Next Steps

1. Verify the SDK exists at workspaces/roboto-sai-sdk
2. Ensure .env file has required environment variables
3. Build the images: .\docker-quick.ps1 build
4. Start development: .\docker-quick.ps1 dev
5. Check logs if issues occur: .\docker-quick.ps1 logs
