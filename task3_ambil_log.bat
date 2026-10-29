@echo off
setlocal enabledelayedexpansion

:: Pindah ke folder lokasi file .bat ini berada
cd /d "%~dp0"

set "LOG_FILE=%~dp0task3_ambil_log.log"

echo ====================================================== >> "%LOG_FILE%"
echo [%DATE% %TIME%] Memulai Task 3: 1_ambil_data_log.py >> "%LOG_FILE%"
echo ====================================================== >> "%LOG_FILE%"

:: Cari lokasi activate.bat Conda
set "ACTIVATE_BAT="
for %%P in (
    "%USERPROFILE%\.conda\Scripts\activate.bat"
    "%USERPROFILE%\miniconda3\Scripts\activate.bat"
    "%USERPROFILE%\Miniconda3\Scripts\activate.bat"
    "%LOCALAPPDATA%\miniconda3\Scripts\activate.bat"
    "%LOCALAPPDATA%\Programs\miniconda3\Scripts\activate.bat"
    "C:\miniconda3\Scripts\activate.bat"
    "C:\ProgramData\miniconda3\Scripts\activate.bat"
    "%USERPROFILE%\anaconda3\Scripts\activate.bat"
    "%USERPROFILE%\Anaconda3\Scripts\activate.bat"
    "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat"
    "C:\anaconda3\Scripts\activate.bat"
    "C:\ProgramData\anaconda3\Scripts\activate.bat"
    "D:\miniconda3\Scripts\activate.bat"
    "E:\miniconda3\Scripts\activate.bat"
    "D:\anaconda3\Scripts\activate.bat"
    "E:\anaconda3\Scripts\activate.bat"
) do (
    if not defined ACTIVATE_BAT (
        if exist "%%~P" set "ACTIVATE_BAT=%%~P"
    )
)

if not defined ACTIVATE_BAT (
    where conda.bat >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%C in ('where conda.bat') do (
            if not defined ACTIVATE_BAT (
                if exist "%%~dpCactivate.bat" set "ACTIVATE_BAT=%%~dpCactivate.bat"
            )
        )
    )
)

if defined ACTIVATE_BAT (
    call "!ACTIVATE_BAT!" maganghub
) else (
    call conda activate maganghub 2>nul
)

:: Jalankan skrip sinkronisasi data log historis
python 1_ambil_data_log.py >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

echo [%DATE% %TIME%] Task 3 selesai dengan exit code: !EXIT_CODE! >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

exit /b !EXIT_CODE!
