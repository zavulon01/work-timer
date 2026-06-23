@echo off
echo ===================================================
echo   Work Timer (Pomodoro) - Build and Setup Script
echo ===================================================
echo.

:: Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH!
    echo Please install Python and try again.
    pause
    exit /b 1
)

:: Create Virtual Environment
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

:: Activate environment and install dependencies
echo.
echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Generate icon files for compile and tray decoration
echo.
echo Generating application icon...
python -c "from PIL import Image, ImageDraw; size=64; img=Image.new('RGBA', (size,size), (0,0,0,0)); draw=ImageDraw.Draw(img); draw.ellipse((8, 14, 56, 58), fill=(255, 107, 107), outline=(230, 80, 80), width=2); draw.polygon([(32, 4), (25, 16), (39, 16)], fill=(46, 196, 182)); draw.rectangle((30, 10, 34, 16), fill=(46, 196, 182)); img.save('icon.png'); img.save('icon.ico')"

:: Compile application with PyInstaller
echo.
echo Compiling application to single executable (timer.exe)...
pyinstaller --noconsole --onefile --collect-all customtkinter --icon=icon.ico --name=timer main.py

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo   BUILD SUCCESSFUL!
    echo   The executable can be found in the "dist" folder.
    echo   Path: dist\timer.exe
    echo ===================================================
) else (
    echo.
    echo Build failed. Please check errors above.
)

pause
