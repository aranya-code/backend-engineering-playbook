@echo off
echo ============================================
echo Starting Celery Worker
echo ============================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo Starting Celery worker...
echo Background tasks will be processed here
echo.

celery -A app.tasks worker --loglevel=info --pool=solo

pause
