@echo off
:: ======================================================================
:: _common.bat — Helper bersama untuk semua task scheduler.
:: Jangan dijalankan langsung; di-"call" oleh task1/2/3.
::
:: Menyediakan:
::   :cari_python   -> set PYTHON_EXE ke python.exe milik env maganghub
:: ======================================================================

:: --- Cari python.exe milik environment "maganghub" ---------------------
:cari_python
set "PYTHON_EXE="
for %%P in (
    "%USERPROFILE%\.conda\envs\maganghub\python.exe"
    "%USERPROFILE%\miniconda3\envs\maganghub\python.exe"
    "%USERPROFILE%\Miniconda3\envs\maganghub\python.exe"
    "%LOCALAPPDATA%\miniconda3\envs\maganghub\python.exe"
    "%LOCALAPPDATA%\Programs\miniconda3\envs\maganghub\python.exe"
    "C:\miniconda3\envs\maganghub\python.exe"
    "C:\ProgramData\miniconda3\envs\maganghub\python.exe"
    "%USERPROFILE%\anaconda3\envs\maganghub\python.exe"
    "%USERPROFILE%\Anaconda3\envs\maganghub\python.exe"
    "%LOCALAPPDATA%\anaconda3\envs\maganghub\python.exe"
    "C:\anaconda3\envs\maganghub\python.exe"
    "C:\ProgramData\anaconda3\envs\maganghub\python.exe"
    "D:\miniconda3\envs\maganghub\python.exe"
    "E:\miniconda3\envs\maganghub\python.exe"
    "D:\anaconda3\envs\maganghub\python.exe"
    "E:\anaconda3\envs\maganghub\python.exe"
) do (
    if not defined PYTHON_EXE (
        if exist "%%~P" set "PYTHON_EXE=%%~P"
    )
)

:: Fallback: conda env list -> ambil path env maganghub
if not defined PYTHON_EXE (
    where conda >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%L in ('conda env list 2^>nul ^| findstr /i "maganghub"') do (
            if not defined PYTHON_EXE (
                for /f "tokens=1" %%E in ("%%L") do (
                    if exist "%%E\python.exe" set "PYTHON_EXE=%%E\python.exe"
                )
            )
        )
    )
)
goto :eof
