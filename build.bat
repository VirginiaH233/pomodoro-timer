@echo off
cd /d "%~dp0"
echo 🍅 Building Pomodoro Timer...
echo.

pyinstaller --onefile --windowed --noconfirm ^
    --name "Pomi" ^
    --collect-all pystray ^
    --collect-all PIL ^
    --hidden-import win32gui ^
    --hidden-import win32con ^
    --hidden-import win32api ^
    --hidden-import pystray._win32 ^
    --hidden-import ctypes ^
    --hidden-import tkinter ^
    --hidden-import lang ^
    --add-data "呼应.mp3;." ^
    --add-data "灵光.mp3;." ^
    main.py

echo.
if %ERRORLEVEL% equ 0 (
    echo ✅ Build succeeded!
    echo 📦 dist\PomodoroTimer.exe
) else (
    echo ❌ Build failed
)
pause
