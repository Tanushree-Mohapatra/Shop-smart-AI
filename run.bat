@echo off
echo ============================================
echo   ShopSmart AI - Starting...
echo ============================================

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install minimal requirements if Flask or flask_cors not found
python -c "import flask, flask_cors, dotenv, PIL" 2>nul || (
    echo Installing dependencies...
    pip install -r requirements_minimal.txt
)

echo.
echo Starting ShopSmart AI on http://localhost:5000
echo Press Ctrl+C to stop.
echo.

python app.py

pause
