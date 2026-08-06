@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\pythonw.exe" (
    echo [ERROR] venv not found. Run "python -m venv venv" first.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] .env file not found.
    echo Copy .env.example to .env and fill in your token and channel IDs.
    pause
    exit /b 1
)

if exist "bridge.pid" (
    echo [WARN] bridge.pid already exists. The bot may already be running.
    echo If you are sure it is not running, delete bridge.pid and try again.
    pause
    exit /b 1
)

echo Starting bot in background, no window, logging to bridge.log ...

for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Start-Process -FilePath 'venv\Scripts\pythonw.exe' -ArgumentList 'bridge_bot.py' -WorkingDirectory '%~dp0' -PassThru).Id"`) do set BOT_PID=%%i

echo %BOT_PID% > bridge.pid
echo Bot started in background. PID: %BOT_PID%
echo Log file: bridge.log
echo Run stop_bridge.bat to stop it.
pause
