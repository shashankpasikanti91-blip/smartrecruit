@echo off
REM This script creates a desktop shortcut for the Recruitment ATS app

setlocal enabledelayedexpansion

REM Get the current directory
cd /d "%~dp0"

REM Define paths
set APP_DIR=%CD%
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_NAME=Recruitment ATS v3.2
set BATCH_FILE=%APP_DIR%\START_APP_DEMO.bat

echo.
echo Creating desktop shortcut: "%SHORTCUT_NAME%"
echo.

REM Create VBS script to create the shortcut
set VBS_FILE=%TEMP%\CreateShortcut.vbs

(
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sDesktop = oWS.SpecialFolders("Desktop"^)
    echo set oLink = oWS.CreateShortcut(sDesktop ^& "\%SHORTCUT_NAME%.lnk"^)
    echo oLink.TargetPath = "%BATCH_FILE%"
    echo oLink.WorkingDirectory = "%APP_DIR%"
    echo oLink.Description = "Recruitment ATS v3.2 - Demo Version"
    echo oLink.WindowStyle = 1
    echo oLink.Save
    echo WScript.Echo "Shortcut created successfully!"
) > "%VBS_FILE%"

REM Execute the VBS script
cscript.exe "%VBS_FILE%"

REM Clean up
del "%VBS_FILE%"

echo.
echo ===================================================================
echo  Desktop shortcut created! 
echo  Look for "Recruitment ATS v3.2.lnk" on your desktop
echo ===================================================================
echo.
pause
