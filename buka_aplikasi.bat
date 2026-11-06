@echo off
:: ======================================================================
:: buka_aplikasi.bat - Launcher GUI Asisten Laporan Harian MagangHub
:: Membuka 2_aplikasi_isi_laporan.py memakai python env "maganghub".
:: ======================================================================
setlocal enabledelayedexpansion
title Asisten Laporan Harian MagangHub
cd /d "%~dp0"

:: --- Cek berkas wajib ------------------------------------------------
if not exist "2_aplikasi_isi_laporan.py" goto :tak_ada_skrip
if not exist ".env" goto :tak_ada_env

:: --- Cari python env maganghub ---------------------------------------
set "PYTHON_EXE="
call "%~dp0_common.bat" :cari_python 2>nul
if not defined PYTHON_EXE (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE goto :tak_ada_python

:: --- Jalankan GUI -----------------------------------------------------
start "" "!PYTHON_EXE!" "2_aplikasi_isi_laporan.py"
exit /b 0

:tak_ada_skrip
echo.
echo [MASALAH] File 2_aplikasi_isi_laporan.py tidak ditemukan di:
echo           "%~dp0"
echo.
echo Pastikan buka_aplikasi.bat berada di dalam folder proyek.
echo Bila ingin meletakkannya di Desktop, buat Shortcut, jangan copy file.
echo.
pause
exit /b 1

:tak_ada_env
echo.
echo [MASALAH] File .env belum ada.
echo           Jalankan SETUP_INSTAL.bat terlebih dahulu.
echo.
pause
exit /b 1

:tak_ada_python
echo.
echo [MASALAH] Python tidak ditemukan.
echo           Jalankan SETUP_INSTAL.bat terlebih dahulu.
echo.
pause
exit /b 1
