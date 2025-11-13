@echo off
echo ================================================
echo   Creating HDVC/SYNCON Vector Database Environment
echo ================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if conda is available
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Conda is not installed or not in PATH
    echo Please install Anaconda/Miniconda and try again
    pause
    exit /b 1
)

echo Creating conda environment from environment_vectordb.yml...
echo.
conda env create -f environment_vectordb.yml

if %errorlevel% neq 0 (
    echo ERROR: Failed to create conda environment
    echo Please check environment_vectordb.yml and try again
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Environment created successfully!
echo ================================================
echo.
echo To activate the environment, run:
echo   conda activate hdvc_syncon_vectordb
echo.
echo To run the vector database creation script:
echo   python build_vectordb_hdvc_syncon.py
echo.
pause