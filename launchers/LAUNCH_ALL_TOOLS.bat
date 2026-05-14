@echo off
REM ============================================================
REM  Buildathon BT190 - Launch ALL Tools in parallel
REM ============================================================
setlocal
pushd "%~dp0.."

echo ========================================
echo   BUILDATHON BT190 - LAUNCH ALL TOOLS
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    pause
    popd & endlocal & exit /b 1
)

echo Launching all tools in separate windows...
echo.

python launchers\TOOL_LAUNCHER.py --all

echo.
echo ========================================
echo All tools launched.
echo ========================================
pause
popd
endlocal
