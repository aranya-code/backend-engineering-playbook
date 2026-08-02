@echo off
echo ============================================
echo Starting FastAPI Redis Lab
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

echo Starting FastAPI application...
echo API will be available at: http://localhost:8000
echo Documentation: http://localhost:8000/docs
echo.

uvicorn app.main:app --reload

pause
