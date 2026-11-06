@echo off
:: ======================================================================
:: Task 2 - Cek Presensi & Notifikasi
:: Dijadwalkan: setiap 30 menit oleh daftar_task_scheduler.bat
:: Menjalankan: maganghub_api.py
:: ======================================================================
setlocal enabledelayedexpansion
title MagangHub - Cek Presensi
cd /d "%~dp0"

set "LOG_FILE=%~dp0task2_cek_presensi.log"
set "SKRIP=maganghub_api.py"
set "ARGS="
set "JUDUL=Task 2 - Cek Presensi & Notifikasi"

echo.>>"%LOG_FILE%"
echo ======================================================>>"%LOG_FILE%"
echo [%DATE% %TIME%] Mulai %JUDUL% : %SKRIP%>>"%LOG_FILE%"
echo ======================================================>>"%LOG_FILE%"

:: --- Cek prasyarat ----------------------------------------------------
if not exist "%SKRIP%" (
    echo [%DATE% %TIME%] GAGAL: %SKRIP% tidak ditemukan di %~dp0>>"%LOG_FILE%"
    echo.
    echo [MASALAH] File %SKRIP% tidak ditemukan di folder ini.
    echo.
    exit /b 1
)

if not exist ".env" (
    echo [%DATE% %TIME%] GAGAL: .env tidak ditemukan>>"%LOG_FILE%"
    echo.
    echo [MASALAH] File .env belum ada.
    echo           Jalankan SETUP_INSTAL.bat terlebih dahulu.
    echo.
    exit /b 1
)

:: --- Cari python env maganghub ---------------------------------------
call "%~dp0_common.bat" :cari_python
if not defined PYTHON_EXE (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
    echo [%DATE% %TIME%] GAGAL: python.exe tidak ditemukan>>"%LOG_FILE%"
    echo.
    echo [MASALAH] Python tidak ditemukan.
    echo           Jalankan SETUP_INSTAL.bat terlebih dahulu.
    echo.
    exit /b 1
)

echo [%DATE% %TIME%] Python: !PYTHON_EXE!>>"%LOG_FILE%"

:: --- Jalankan ---------------------------------------------------------
"!PYTHON_EXE!" "%SKRIP%" %ARGS% >>"%LOG_FILE%" 2>&1
set "EXIT_CODE=!ERRORLEVEL!"

echo [%DATE% %TIME%] %JUDUL% selesai, exit code: !EXIT_CODE!>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"
exit /b !EXIT_CODE!
