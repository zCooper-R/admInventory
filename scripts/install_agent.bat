@echo off
REM ============================================================
REM IT Inventory Agent — Self-Installer for Windows
REM ============================================================
REM Run this file ONCE as Administrator on the target computer.
REM It will:
REM   1. Copy the agent script to a permanent location
REM   2. Create a weekly scheduled task (runs every Monday 09:00)
REM   3. Run the agent immediately for the first scan
REM
REM No user interaction required after this — the task runs
REM automatically in the background under the SYSTEM account.
REM ============================================================

REM ── You must edit these two lines before distributing ────────
SET API_URL=http://YOUR-SERVER-ADDRESS/api/v1/devices/sync/
SET API_KEY=change-me-before-production
REM ────────────────────────────────────────────────────────────

SET TASK_NAME=IT_Inventory_Agent
SET INSTALL_DIR=%ProgramFiles%\ITInventoryAgent

echo.
echo  ============================================
echo   IT Inventory Agent Installer
echo  ============================================
echo.

REM ── Check admin privileges ───────────────────────────────────
net session >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: This installer must be run as Administrator.
    echo  Right-click the file and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

REM ── Check PowerShell ─────────────────────────────────────────
where powershell.exe >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: PowerShell not found. This tool requires PowerShell 3+.
    pause
    exit /b 1
)

echo  [1/4] Creating installation directory...
IF NOT EXIST "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo  [2/4] Copying agent script...
copy /Y "%~dp0agent.ps1" "%INSTALL_DIR%\agent.ps1" >nul

REM ── Patch the API URL and key into the installed copy ────────
powershell -Command ^
  "(Get-Content '%INSTALL_DIR%\agent.ps1') ^
   -replace 'http://YOUR-SERVER-ADDRESS/api/v1/devices/sync/', '%API_URL%' ^
   -replace 'change-me-before-production', '%API_KEY%' ^
   | Set-Content '%INSTALL_DIR%\agent.ps1' -Encoding UTF8"

echo  [3/4] Registering scheduled task (weekly, Monday 09:00, SYSTEM account)...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
schtasks /create /f ^
  /tn "%TASK_NAME%" ^
  /tr "powershell.exe -ExecutionPolicy Bypass -NonInteractive -File \"%INSTALL_DIR%\agent.ps1\"" ^
  /sc WEEKLY /d MON /st 09:00 ^
  /ru SYSTEM /rl HIGHEST ^
  /description "IT Inventory hardware collection agent"

IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Failed to create scheduled task.
    pause
    exit /b 1
)

echo  [4/4] Running first scan now...
powershell.exe -ExecutionPolicy Bypass -NonInteractive -File "%INSTALL_DIR%\agent.ps1"

echo.
echo  ============================================
echo   Installation complete!
echo   Agent will run every Monday at 09:00.
echo   Log: %TEMP%\it_inventory_agent.log
echo  ============================================
echo.
pause
