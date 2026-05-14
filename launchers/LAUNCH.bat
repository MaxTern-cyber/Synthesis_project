@echo off
REM ============================================================
REM  Synthesis Project Launcher
REM  Anchors to repo root regardless of where this script is run
REM ============================================================
setlocal
pushd "%~dp0.."

echo ===============================================
echo    SYNTHESIS PROJECT - LAUNCHER
echo ===============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH.
    pause
    popd & endlocal & exit /b 1
)

echo Choose an option:
echo   1. Hardware Debug Assistant   (port 8610)
echo   2. Netlist Analyzer           (port 8620)
echo   3. RTL Analyzer               (port 8630)
echo   4. Advanced Debugger          (port 8640)
echo   5. DAG Visualizer             (port 8650)
echo   6. Launch ALL demos
echo   7. System status check
echo   0. Exit
echo.

set /p choice="Enter your choice: "

if "%choice%"=="1" goto demo1
if "%choice%"=="2" goto demo2
if "%choice%"=="3" goto demo3
if "%choice%"=="4" goto demo4
if "%choice%"=="5" goto demo5
if "%choice%"=="6" goto all
if "%choice%"=="7" goto check
if "%choice%"=="0" goto end

echo Invalid choice!
goto end

:demo1
start "Hardware Debug Assistant" cmd /k "cd /d %CD%\tools\demo3 && streamlit run debug_assistant.py --server.port 8610"
echo Launched at http://localhost:8610
goto end

:demo2
start "Netlist Analyzer" cmd /k "cd /d %CD%\tools\demo2 && streamlit run local_analyzer.py --server.port 8620"
echo Launched at http://localhost:8620
goto end

:demo3
start "RTL Analyzer" cmd /k "cd /d %CD%\tools\rtl_analyzer && streamlit run rtl_analyzer.py --server.port 8630"
echo Launched at http://localhost:8630
goto end

:demo4
start "Advanced Debugger" cmd /k "cd /d %CD%\tools\final_debugger && streamlit run advanced_debugger.py --server.port 8640"
echo Launched at http://localhost:8640
goto end

:demo5
start "DAG Visualizer" cmd /k "cd /d %CD%\tools\dag_visualizer && streamlit run dag_visualizer.py --server.port 8650"
echo Launched at http://localhost:8650
goto end

:all
start "Hardware Debug Assistant" cmd /k "cd /d %CD%\tools\demo3 && streamlit run debug_assistant.py --server.port 8610"
start "Netlist Analyzer"         cmd /k "cd /d %CD%\tools\demo2 && streamlit run local_analyzer.py --server.port 8620"
start "RTL Analyzer"             cmd /k "cd /d %CD%\tools\rtl_analyzer && streamlit run rtl_analyzer.py --server.port 8630"
start "Advanced Debugger"        cmd /k "cd /d %CD%\tools\final_debugger && streamlit run advanced_debugger.py --server.port 8640"
echo.
echo All demos launched:
echo   Hardware Debug Assistant: http://localhost:8610
echo   Netlist Analyzer:         http://localhost:8620
echo   RTL Analyzer:             http://localhost:8630
echo   Advanced Debugger:        http://localhost:8640
goto end

:check
python launchers\PRESENTATION_LAUNCHER.py --check
goto end

:end
echo.
pause
popd
endlocal
