@echo off
REM Stop the Kartify Order Assistant web UI started by start.bat / start.sh.
REM   stop.bat           stops whatever is listening on port 8501
REM   stop.bat 8502      another port
setlocal EnableDelayedExpansion
set PORT=%~1
if "%PORT%"=="" set PORT=8501

set FOUND=
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
    REM The same PID shows up once for IPv4 and once for IPv6.
    if not "%%p"=="!LAST!" (
        set FOUND=1
        echo Stopping process %%p on port %PORT%
        taskkill /PID %%p /T /F >nul 2>nul
    )
    set LAST=%%p
)

if not defined FOUND echo Nothing is listening on port %PORT%.
exit /b 0
