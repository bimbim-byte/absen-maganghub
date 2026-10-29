@echo off
setlocal enabledelayedexpansion
title Login MagangHub
cd /d "%~dp0"

echo ======================================================================
echo                     LOGIN MAGANGHUB
echo ======================================================================
echo.
echo  Browser akan terbuka. Silakan login seperti biasa.
echo  Setelah masuk halaman dashboard, sesi tersimpan otomatis.
echo  Tutup jendela browser bila sudah selesai.
echo.

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

if not defined ACTIVATE_BAT (
    echo [GAGAL] Miniconda / Anaconda tidak ditemukan.
    echo         Jalankan SETUP_INSTAL.bat lebih dahulu.
    echo.
    pause
    exit /b 1
)

call "!ACTIVATE_BAT!" maganghub
if not defined CONDA_PREFIX (
    echo [GAGAL] Environment maganghub belum siap.
    echo         Jalankan SETUP_INSTAL.bat lebih dahulu.
    echo.
    pause
    exit /b 1
)

echo %CONDA_PREFIX% | findstr /i /e "\maganghub" >nul
if errorlevel 1 (
    echo [GAGAL] Environment maganghub belum siap.
    echo         Jalankan SETUP_INSTAL.bat lebih dahulu.
    echo.
    pause
    exit /b 1
)

python login_browser.py

echo.
echo ----------------------------------------------------------------------
echo  Selesai. File token.json sudah diperbarui.
echo  Berikutnya jalankan buka_aplikasi.bat
echo ----------------------------------------------------------------------
echo.
pause
endlocal