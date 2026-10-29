@echo off
setlocal enabledelayedexpansion
title Asisten Laporan Harian MagangHub

:: 1. Tentukan lokasi folder proyek
set "APP_DIR=%~dp0"
if not exist "%APP_DIR%2_aplikasi_isi_laporan.py" (
    echo.
    echo [MASALAH] File 2_aplikasi_isi_laporan.py tidak ditemukan di:
    echo           "%APP_DIR%"
    echo.
    echo Pastikan buka_aplikasi.bat berada di dalam folder proyek.
    echo Bila ingin meletakkannya di Desktop, buat Shortcut (bukan copy file).
    echo.
    pause
    exit /b 1
)
cd /d "%APP_DIR%"

:: 2. Cari lokasi activate.bat Conda - tidak bergantung pada lokasi pemasangan
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
    echo.
    echo [MASALAH] Miniconda / Anaconda tidak ditemukan.
    echo           Jalankan SETUP_INSTAL.bat lebih dahulu.
    echo.
    pause
    exit /b 1
)

:: 3. Aktifkan Conda environment maganghub
call "!ACTIVATE_BAT!" maganghub

if not defined CONDA_PREFIX (
    echo.
    echo [MASALAH] Environment "maganghub" belum siap.
    echo           Jalankan SETUP_INSTAL.bat lebih dahulu.
    echo.
    pause
    exit /b 1
)

echo %CONDA_PREFIX% | findstr /i /e "\maganghub" >nul
if errorlevel 1 (
    echo.
    echo [MASALAH] Environment "maganghub" belum siap.
    echo           Jalankan SETUP_INSTAL.bat lebih dahulu.
    echo.
    pause
    exit /b 1
)

:: 4. Buka aplikasi GUI menggunakan pythonw - tanpa jendela hitam CMD yang menggantung
start "" pythonw 2_aplikasi_isi_laporan.py

:: 5. Tutup jendela launcher
endlocal
exit
