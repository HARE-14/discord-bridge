@echo off
cd /d "%~dp0"

if not exist "bridge.log" (
    echo bridge.log not found yet. Start the bot first.
    pause
    exit /b 1
)

echo Tailing bridge.log (Ctrl+C to stop watching, this does not stop the bot)...
powershell -NoProfile -Command "Get-Content -Path 'bridge.log' -Wait -Tail 30"
