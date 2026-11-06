@echo off
:: ======================================================================
:: Task 1 - Isi Daily Log Otomatis
:: Dijadwalkan: setiap hari pukul 22:00 oleh daftar_task_scheduler.bat
:: Menjalankan: 3_isi_otomatis.py --submit
:: ======================================================================
setlocal enabledelayedexpansion
title MagangHub - Isi Log Otomatis
cd /d "%~dp0"

set "LOG_FILE=%~dp0task1_isi_otomatis.log"
set "SKRIP=3_isi_otomatis.py"
set "ARGS=--submit"
set "JUDUL=Task 1 - Isi Daily Log Otomatis"

echo.>>"%LOG_FILE%"
echo ======================================================>>"%LOG_FILE%"
echo [%DATE% %TIME%] Mulai %JUDUL% : %SKRIP% %ARGS%>>"%LOG_FILE%"
echo ======================================================>>"%LOG_FILE%"

:: --- Cek prasyarat ----------------------------------------------------
if not exist "%SKRIP%" (
    echo [%DATE% %TIME%] GAGAL: %SKRIP% tidak ditemukan di %~dp0>>"%LOG_FILE%"
    echo.
    echo [MASALAH] File %SKRIP% tidak ditemukan di folder ini.
    echo           Pastikan semua file aplikasi berada di folder yang sama.
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
