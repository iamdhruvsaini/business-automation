@echo off
setlocal enabledelayedexpansion

REM Agent Pipeline Setup Script for Windows
REM This script helps you set up Agent Pipeline quickly

echo.
echo [Agent Pipeline Setup]
echo ======================

REM Check prerequisites
echo [INFO] Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first:
    echo    https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose is not available. Please install Docker Desktop which includes Compose.
        pause
        exit /b 1
    )
)

echo [OK] Docker is installed

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [OK] Docker is running

REM Check Python environment inside Docker
echo.
echo [INFO] Setting up Python environment for Docker development...
echo [INFO] You can use the following commands inside Docker containers:
echo   - pip install -r requirements.txt
echo   - uv sync (if using uv for dependency management)
echo   - python -m venv venv ^&^& venv\Scripts\activate (for local venv)

REM Check for .env file and GROQ_API_KEY
echo.
echo [INFO] Checking API key configuration...

if not exist .env (
    echo [WARN] No .env file found. Creating one...
    (
        echo # Agent Pipeline Configuration
        echo GROQ_API_KEY=your_groq_key_here
        echo.
        echo # Optional settings ^(defaults shown^)
        echo GROQ_MODEL=llama3-70b-8192
        echo MONGODB_URI=mongodb://admin:password@mongodb:27017/
        echo MONGODB_DATABASE=agent
        echo LOG_LEVEL=INFO
    ) > .env
    echo [OK] Created .env file
)

findstr /C:"your_groq_key_here" .env >nul
if not errorlevel 1 goto ask_key

findstr /C:"GROQ_API_KEY=" .env >nul
if errorlevel 1 goto ask_key

findstr /C:"GROQ_API_KEY=$" .env >nul
if not errorlevel 1 goto ask_key

goto key_ok

:ask_key
echo.
echo [ERROR] GROQ_API_KEY not configured properly
echo.
echo Please get your free Groq API key:
echo 1. Visit: https://console.groq.com/
echo 2. Sign up/login
echo 3. Go to API Keys section
echo 4. Create a new API key
echo 5. Copy the key ^(starts with 'gsk_'^)
echo.
set /p groq_key=Enter your Groq API key: 

REM Update .env file
powershell -Command "(Get-Content .env) -replace 'GROQ_API_KEY=.*', 'GROQ_API_KEY=%groq_key%' | Set-Content .env"

echo [OK] API key saved to .env file

:key_ok
echo [OK] API key is configured

REM Start services
echo.
echo [INFO] Starting Agent Pipeline services...
echo This may take a few minutes on first run...

REM Install Python dependencies if requirements.txt exists
if exist requirements.txt (
    echo [INFO] Installing Python dependencies...
    echo [CMD] pip install -r requirements.txt
)

REM Check for uv and sync dependencies
if exist pyproject.toml (
    echo [INFO] pyproject.toml found - you can use uv for dependency management
    echo [CMD] uv sync
)

docker-compose down >nul 2>&1
docker-compose up -d

echo.
echo [INFO] Waiting for services to start...

REM Wait for API to be ready
set max_attempts=30
set attempt=0

:wait_loop
if !attempt! geq !max_attempts! goto timeout

curl -s http://localhost:8000/health >nul 2>&1
if not errorlevel 1 goto api_ready

set /a attempt+=1
timeout /t 2 /nobreak >nul
echo|set /p="."
goto wait_loop

:timeout
echo.
echo [ERROR] API failed to start within 60 seconds
echo Check logs with: docker-compose logs api
pause
exit /b 1

:api_ready
echo.

REM Test Database
curl -s http://localhost:8000/db/health | findstr "healthy" >nul
if not errorlevel 1 (
    echo [OK] MongoDB: Connected
) else (
    echo [WARN] MongoDB: Check connection
)

REM Check n8n
curl -s http://localhost:5678 >nul 2>&1
if not errorlevel 1 (
    echo [OK] n8n Workflows: http://localhost:5678
) else (
    echo [WARN] n8n Workflows: Starting up...
)

echo.
echo [SUCCESS] Setup complete!
echo.
echo [Commands] Quick Commands:
echo    API Docs:     http://localhost:8000/docs
echo    n8n Flows:    http://localhost:5678
echo    View Logs:    docker-compose logs -f
echo    Stop All:     docker-compose down
echo.
echo [Python] Development Commands:
echo    Connect to container: docker exec -it project-api-1 bash
echo    Install deps:         pip install -r requirements.txt
echo    UV sync:             uv sync
echo    Activate venv:        python -m venv venv ^&^& venv\Scripts\activate
echo.
echo [Test] Test with sample data:
echo    curl -X POST http://localhost:8000/pipeline/process-all/demo
echo.
echo [Docs] Full documentation in README.md
echo.
pause