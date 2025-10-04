@echo off
REM Unified AI Chat - Start All Services (Windows)

echo Starting Unified AI Chat System...
echo.

REM Check prerequisites
where java >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Java not found. Please install Java 11 or higher.
    exit /b 1
)

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: npm not found. Please install Node.js 14 or higher.
    exit /b 1
)

echo All prerequisites met
echo.

REM Start Absence Management Backend
echo Starting Absence Management Backend...
cd ..\ai_absence-ai_absence_mi\backend\absence-management
start "Absence Backend" cmd /c "mvnw.cmd spring-boot:run"
cd ..\..\..\unified_ai_chat
timeout /t 30 /nobreak >nul

REM Start Unified Chat Backend
echo Starting Unified Chat Backend...
cd backend

if not exist .env (
    echo Warning: .env file not found. Creating from example...
    copy .env.example .env
    echo Please edit backend\.env and add your GEMINI_API_KEY
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt
start "Unified Backend" cmd /c "python unified_chat_server.py"
cd ..
timeout /t 10 /nobreak >nul

REM Start React Frontend
echo Starting React Frontend...
cd frontend

if not exist .env (
    echo Creating .env from example...
    copy .env.example .env
)

if not exist node_modules (
    echo Installing npm dependencies...
    call npm install
)

start "React Frontend" cmd /c "npm start"
cd ..

echo.
echo ===================================================
echo All services started successfully!
echo ===================================================
echo.
echo Services running:
echo   - Absence Management: http://localhost:8080
echo   - Unified Backend:    http://localhost:5002
echo   - React Frontend:     http://localhost:3000
echo.
echo Opening browser...
timeout /t 5 /nobreak >nul
start http://localhost:3000
