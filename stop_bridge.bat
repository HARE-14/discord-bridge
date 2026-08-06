@echo off
cd /d "%~dp0"

if not exist "bridge.pid" (
    echo No bridge.pid file found. The bot may not be running, or was started differently.
    pause
    exit /b 1
)

set /p BOT_PID=<bridge.pid

echo Stopping bot process (PID %BOT_PID%)...
taskkill /PID %BOT_PID% /F >nul 2>&1

if %ERRORLEVEL%==0 (
    echo Bot stopped.
) else (
    echo Could not find process with PID %BOT_PID%. It may already be stopped.
)

del bridge.pid
pause
