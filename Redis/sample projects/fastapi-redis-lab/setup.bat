@echo off
echo ============================================
echo FastAPI Redis Lab - Setup Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Step 3: Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Step 4: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo Step 5: Creating environment file...
if not exist ".env" (
    copy .env.example .env
    echo .env file created from template
) else (
    echo .env file already exists
)
echo.

echo Step 6: Seeding database with sample data...
python seed_data.py seed
echo.

echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Make sure Redis is running
echo   2. Run: start_server.bat
echo   3. Open: http://localhost:8000/docs
echo.
echo Optional:
echo   - Run Celery worker: start_celery.bat
echo   - Test APIs: python test_api.py
echo.

pause
