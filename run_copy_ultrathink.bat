@echo off
echo ================================================
echo   HDVC & SYNCON File Copy Script
echo   Copying files from G:\ultrathink (1 year data)
echo ================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if source directory exists
if not exist "G:\ultrathink" (
    echo ERROR: Source directory G:\ultrathink not found
    echo Please check that the G: drive is connected and ultrathink folder exists
    pause
    exit /b 1
)

REM Run the copy script
echo Starting file copy process...
echo.
python copy_ultrathink_subset.py

echo.
echo Copy process completed!
echo Check the data/pdfs/ folders for copied files
echo Review copy_manifest.json for detailed results
echo.
pause