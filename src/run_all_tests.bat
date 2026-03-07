@echo off
echo ============================================
echo   Volunteer Scheduler - Automated Test Run
echo ============================================

echo Initializing virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing test dependencies...
pip install pytest requests pyautogui pillow

echo Starting API server...
start "" python api.py
echo Waiting for API to start...
timeout /t 5 >nul

echo Running API + DB tests...
pytest test_api.py --maxfail=1 --disable-warnings -q
pytest test_database.py --maxfail=1 --disable-warnings -q

echo Running GUI automation tests...
pytest test_gui.py --maxfail=1 --disable-warnings -q

echo Killing API server...
taskkill /IM python.exe /F >nul 2>&1

echo ============================================
echo   ALL TESTS COMPLETE
echo ============================================
pause