@echo off
setlocal enabledelayedexpansion
cls

:: --- Configuration ---
:: This batch file is designed to organize the folder it is currently in.

:: Set the full path to your python.exe if it's not in your system's PATH.
set "PYTHON_EXE=python"

:: The Python script is expected to be in the SAME folder as this .bat file.
set "SCRIPT_PATH=%~dp0organize_by_handle.py"

:: The folder to organize IS the folder this batch file is in.
set "TARGET_FOLDER=%~dp0"
set "TARGET_FOLDER=%TARGET_FOLDER:~0,-1%"


:: --- Main Logic ---
echo ===============================================
echo  Image Organizer (Strict Start, Min Count 2)
echo ===============================================
echo.
echo This script will organize all images inside THIS FOLDER:
echo "%TARGET_FOLDER%"
echo.

:: Check if the Python script exists before running
if not exist "%SCRIPT_PATH%" (
    echo ERROR: The script 'organize_by_handle.py' was not found in this folder.
    echo Please make sure both the .bat file and the .py file are in the same directory.
    echo.
    pause
    exit /b
)

:: --- User Interaction ---

:: 1. Ask for Dry Run mode
set "DRY_RUN_ARG="
set "RUN_MODE=LIVE RUN (Files will be moved)"
set /p "DRY_RUN_CHOICE=Run in DRY-RUN mode (preview changes without moving)? [Y/N]: "
if /i "%DRY_RUN_CHOICE%"=="Y" (
    set "DRY_RUN_ARG=--dry-run"
    set "RUN_MODE=DRY-RUN (Preview Only)"
)
echo.

:: 2. Ask to create a log file
set "LOG_ARG="
set "LOG_STATUS=Disabled"
set /p "LOG_CHOICE=Create a CSV log file of all actions? [Y/N]: "
if /i "%LOG_CHOICE%"=="Y" (
    :: This robust method avoids issues with regional date/time formats.
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "dt=%%I"
    set "YYYY=!dt:~0,4!"
    set "MM=!dt:~4,2!"
    set "DD=!dt:~6,2!"
    set "HH=!dt:~8,2!"
    set "MIN=!dt:~10,2!"
    set "SEC=!dt:~12,2!"

    :: CORRECTED: Use delayed expansion (!) to build the filename from variables set just above.
    set "LOG_FILENAME=organizer_log_!YYYY!!MM!!DD!_!HH!!MIN!!SEC!.csv"
    
    :: CORRECTED: Use delayed expansion (!) to use the LOG_FILENAME variable that was just created.
    set "LOG_ARG=--log "!TARGET_FOLDER!\!LOG_FILENAME!""
    set "LOG_STATUS=Enabled (!LOG_FILENAME!)"
)
echo.


:: --- Execution ---
echo ===============================================
echo  Starting Script with the Following Settings:
echo ===============================================
echo.
echo      Target Folder: "%TARGET_FOLDER%"
echo      Run Mode:      %RUN_MODE%
echo      Logging:       !LOG_STATUS!
echo.

echo Press any key to begin...
pause >nul
echo.

echo Running the script with options: --strict-start --min-count 2 %DRY_RUN_ARG% %LOG_ARG%
echo.
echo --- SCRIPT OUTPUT START ---
:: The quotes around paths ensure spaces are handled correctly.
%PYTHON_EXE% "%SCRIPT_PATH%" "%TARGET_FOLDER%" --strict-start --min-count 2 %DRY_RUN_ARG% %LOG_ARG%
echo --- SCRIPT OUTPUT END ---
echo.
echo.
echo The script has finished.

pause