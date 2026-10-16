@echo off
REM Start the Kartify Order Assistant locally.
REM   start.bat          web UI on http://localhost:8501
REM   start.bat cli      command-line chat (extra args are passed to main.py)
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv || goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

if not exist "config.json" if "%OPENAI_API_KEY%"=="" (
    echo No config.json or OPENAI_API_KEY found.
    echo Copy config.example.json to config.json and add your OpenAI key.
    exit /b 1
)

if /i "%~1"=="cli" goto :cli
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501
exit /b %errorlevel%

:cli
shift
".venv\Scripts\python.exe" main.py %1 %2 %3 %4 %5 %6
exit /b %errorlevel%

:error
echo Setup failed.
exit /b 1
