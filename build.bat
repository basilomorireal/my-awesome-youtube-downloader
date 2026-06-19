@echo off
echo ============================================
echo  YT Downloader - Build Script
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install pyinstaller pillow pycaw comtypes --quiet

echo [2/3] Converting icon...
python -c "from PIL import Image; img=Image.open('assets\icons\icon.png').convert('RGBA'); img.save('assets\icons\icon.ico',format='ICO',sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])" 2>nul

echo [3/3] Building exe...
echo.

set ARGS=--onefile --windowed --name "YT Downloader"
set ARGS=%ARGS% --icon=assets\icons\icon.ico

:: Assets
set ARGS=%ARGS% --add-data "assets\icons\icon.png;assets\icons"
set ARGS=%ARGS% --add-data "assets\icons\icon.ico;assets\icons"
set ARGS=%ARGS% --add-data "assets\images\title.gif;assets\images"
set ARGS=%ARGS% --add-data "assets\images\cat.png;assets\images"

if exist "assets\audio\theme.mp3"      set ARGS=%ARGS% --add-data "assets\audio\theme.mp3;assets\audio"
if exist "assets\images\download.gif"  set ARGS=%ARGS% --add-data "assets\images\download.gif;assets\images"
if exist "assets\images\download2.gif" set ARGS=%ARGS% --add-data "assets\images\download2.gif;assets\images"
if exist "assets\images\download3.gif" set ARGS=%ARGS% --add-data "assets\images\download3.gif;assets\images"

:: Binaries
if exist "bin\yt-dlp.exe"  set ARGS=%ARGS% --add-binary "bin\yt-dlp.exe;bin"
if exist "bin\ffmpeg.exe"  set ARGS=%ARGS% --add-binary "bin\ffmpeg.exe;bin"
if exist "bin\ffplay.exe"  set ARGS=%ARGS% --add-binary "bin\ffplay.exe;bin"

python -m PyInstaller %ARGS% src\yt_downloader.py

echo.
echo [DONE]
echo.
echo Your exe is at: dist\YT Downloader.exe
echo.
pause
