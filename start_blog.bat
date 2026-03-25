@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%" || exit /b 1

if not defined LOCALAPPDATA (
    set "LOG_BASE=%USERPROFILE%\AppData\Local"
) else (
    set "LOG_BASE=%LOCALAPPDATA%"
)

set "LOG_DIR=%LOG_BASE%\PersonalBlog\logs"
set "LOG_FILE=%LOG_DIR%\startup.log"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "PYTHON_EXE="
set "MAIN_SCRIPT=%ROOT_DIR%main.py"
set "PYTHONIOENCODING=utf-8"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

"%POWERSHELL_EXE%" -NoProfile -Command "$listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners(); if ($listeners | Where-Object { $_.Port -eq 10024 }) { exit 0 } else { exit 1 }" >nul 2>&1
if %ERRORLEVEL%==0 (
    call :log "already running on port 10024"
    exit /b 0
)

call :log "launcher start"

if not exist "%MAIN_SCRIPT%" (
    call :log "ERROR: main.py not found"
    exit /b 1
)

if exist "%ROOT_DIR%.venv\Scripts\python.exe" set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    for /f "usebackq delims=" %%I in (`where python 2^>nul`) do if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
)

if not defined PYTHON_EXE (
    call :log "ERROR: python interpreter not found"
    exit /b 1
)

call :log "starting main.py with %PYTHON_EXE%"
"%POWERSHELL_EXE%" -NoProfile -Command "& { & $env:PYTHON_EXE $env:MAIN_SCRIPT 2>&1 | ForEach-Object { [System.IO.File]::AppendAllText($env:LOG_FILE, $_.ToString() + [Environment]::NewLine, [System.Text.Encoding]::UTF8) }; exit $LASTEXITCODE }"
set "EXIT_CODE=%ERRORLEVEL%"
call :log "process exited with code %EXIT_CODE%"
exit /b %EXIT_CODE%

:log
setlocal
set "LOG_MESSAGE=%~1"
"%POWERSHELL_EXE%" -NoProfile -Command "$stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'; [System.IO.File]::AppendAllText($env:LOG_FILE, '[' + $stamp + '] ' + $env:LOG_MESSAGE + [Environment]::NewLine, [System.Text.Encoding]::UTF8)" >nul 2>&1
if errorlevel 1 >>"%LOG_FILE%" echo [unknown-time] %LOG_MESSAGE%
endlocal
exit /b 0
