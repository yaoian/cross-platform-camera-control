@echo off
echo ========================================
echo Cross-Platform Camera Control Tool
echo Quick Start Guide
echo ========================================

echo.
echo 🚀 Welcome to Cross-Platform Camera Control Tool!
echo.

echo Step 1: Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)
python --version

echo.
echo Step 2: Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 3: Running demo...
echo ========================================
python demo.py

echo.
echo ========================================
echo Quick Start Commands:
echo ========================================
echo.
echo 📋 List all devices:
echo python v4l2_ctl_cross.py --list-devices
echo.
echo 🎥 Show device formats:
echo python v4l2_ctl_cross.py -d /dev/video0 --list-formats-ext
echo.
echo 🎛️  Show device controls:
echo python v4l2_ctl_cross.py -d /dev/video0 -L
echo.
echo 🔧 Set brightness:
echo python v4l2_ctl_cross.py -d /dev/video0 -c brightness=50
echo.
echo ❓ Show help:
echo python v4l2_ctl_cross.py -h
echo.
echo ========================================
echo Try these commands now!
echo ========================================

pause
