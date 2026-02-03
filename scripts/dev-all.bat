@echo off
REM Roboto SAI Development Environment Setup
REM Start all services locally (without Docker)

echo 🚀 Starting Roboto SAI Development Environment
echo =============================================

REM Start backend (Python)
echo Starting backend API server...
start "Roboto Backend" cmd /k "cd backend && python main_modular.py"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start OS Agent (Node.js)
echo Starting OS Agent (MCP Host)...
start "Roboto OS Agent" cmd /k "cd os-agent && npm run dev"

REM Wait for OS Agent to start
timeout /t 3 /nobreak >nul

REM Build MCP servers
echo Building MCP servers...
cd mcp-servers\fs-server && npm run build
cd ..\..

REM Start MCP filesystem server
echo Starting MCP filesystem server...
start "MCP FS Server" cmd /k "cd mcp-servers\fs-server && npm start"

REM Start frontend (Vite)
echo Starting frontend development server...
start "Roboto Frontend" cmd /k "npm run dev"

echo.
echo ✅ All services starting...
echo.
echo 🔗 Service URLs:
echo    Frontend:    http://localhost:8080
echo    Backend:     http://localhost:5000
echo    OS Agent:    http://localhost:5055
echo    MCP FS:      Running in background
echo.
echo Press any key to stop all services...
pause >nul

REM Stop all services
echo Stopping all services...
taskkill /im node.exe /f >nul 2>&1
taskkill /im python.exe /f >nul 2>&1
echo ✅ All services stopped