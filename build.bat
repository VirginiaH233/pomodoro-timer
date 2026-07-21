@echo off
cd /d "%~dp0"
echo 🍅 Building Pomodoro Timer...
echo.

pyinstaller --onefile --windowed --noconfirm ^
    --name "PomodoroTimer" ^
    --add-data "README.md;." ^
    --collect-all pystray ^
    --collect-all PIL ^
    --hidden-import win32gui ^
    --hidden-import win32con ^
    --hidden-import win32api ^
    --hidden-import pystray._win32 ^
    --hidden-import ctypes ^
    --hidden-import tkinter ^
    main.py

echo.
if %ERRORLEVEL% equ 0 (
    echo ✅ Build succeeded!
    echo 📦 dist\PomodoroTimer.exe
) else (
    echo ❌ Build failed
)
pause
