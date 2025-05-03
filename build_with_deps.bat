@echo off
echo ===================================
echo Oblivion Console Manager Build Tool
echo ===================================
echo.

REM Set up logging
set LOG_FILE=build_debug.log
echo Build started at %date% %time% > %LOG_FILE%
echo. >> %LOG_FILE%

REM Clean previous build files
echo Cleaning previous build files...
echo Cleaning previous build files... >> %LOG_FILE%
if exist build rmdir /s /q build 2>> %LOG_FILE%
if exist dist rmdir /s /q dist 2>> %LOG_FILE%

echo.
echo Building Oblivion Console Manager...
echo.
echo Building Oblivion Console Manager at %date% %time% >> %LOG_FILE%
echo. >> %LOG_FILE%

REM Try a different approach with recursive data folders
echo Running PyInstaller with recursive data folders...
pyinstaller --name="Oblivion Console Manager" ^
    --onefile ^
    --icon=icons/oblivion.png ^
    --noconsole ^
    --add-data="styles.qss;." ^
    --add-data="icons;icons" ^
    --add-data="data;data" ^
    --add-data="styles.qss;." ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.sip ^
    --hidden-import=pyautogui ^
    --hidden-import=psutil ^
    --hidden-import=json_loader ^
    --hidden-import=game_connector ^
    --hidden-import=ui_builder ^
    --hidden-import=enhanced_ui_main ^
    --exclude-module=PyQt5 ^
    --exclude-module=PySide2 ^
    --exclude-module=PySide6 ^
    app.py >> %LOG_FILE% 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build failed! Please check the error messages in %LOG_FILE%
    echo.
    echo Build failed at %date% %time% >> %LOG_FILE%
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo.
echo Build completed successfully at %date% %time% >> %LOG_FILE%

REM Check if executable was created
if exist "dist\Oblivion Console Manager.exe" (
    echo Final executable found at %date% %time% >> %LOG_FILE%
    echo.
    echo Your standalone application is ready in the dist folder!
    echo The EXE file contains all necessary resources.
    
    REM Get file size information
    for %%F in ("dist\Oblivion Console Manager.exe") do (
        echo Executable size: %%~zF bytes >> %LOG_FILE%
        echo Executable size: %%~zF bytes
    )
) else (
    echo.
    echo WARNING: Executable not found in expected location.
    echo Please check the build log (%LOG_FILE%) for errors.
    echo WARNING: Executable not found at %date% %time% >> %LOG_FILE%
)

echo.
echo Build process completed. Debug log saved to %LOG_FILE%
echo.
pause