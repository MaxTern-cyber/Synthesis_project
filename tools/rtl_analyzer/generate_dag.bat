@echo off
REM Standalone DAG Visualization Generator
REM Usage: generate_dag.bat <verilog_file> [output_file]

setlocal

if "%~1"=="" (
    echo Error: No Verilog file specified
    echo Usage: generate_dag.bat ^<verilog_file^> [output_file]
    echo Example: generate_dag.bat netlist.v dag.html
    exit /b 1
)

set VERILOG_FILE=%~1
set OUTPUT_FILE=%~2

if "%OUTPUT_FILE%"=="" (
    set OUTPUT_FILE=dag_visualization.html
)

echo ============================================================
echo   Generating DAG Visualization
echo ============================================================
echo Input: %VERILOG_FILE%
echo Output: %OUTPUT_FILE%
echo.

REM Find Python in virtual environment or use system Python
if exist "..\venv\Scripts\python.exe" (
    "..\venv\Scripts\python.exe" generate_dag_visualization.py "%VERILOG_FILE%" --output "%OUTPUT_FILE%"
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" generate_dag_visualization.py "%VERILOG_FILE%" --output "%OUTPUT_FILE%"
) else (
    python generate_dag_visualization.py "%VERILOG_FILE%" --output "%OUTPUT_FILE%"
)

if %ERRORLEVEL%==0 (
    echo.
    echo Opening visualization in browser...
    start "" "%OUTPUT_FILE%"
)

endlocal
