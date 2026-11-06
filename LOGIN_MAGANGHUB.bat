@echo off
:: ======================================================================
:: LOGIN_MAGANGHUB.bat - Login SSO / perpanjang sesi MagangHub
:: Membuka browser Chrome via Playwright (login_browser.py).
:: ======================================================================
setlocal enabledelayedexpansion
title Login MagangHub
cd /d "%~dp0"

if not exist "login_browser.py" (
    echo.
    echo [MASALAH] File login_browser.py tidak ditemukan di folder ini.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo [MASALAH] File .env belum ada.
    echo           Jalankan SETUP_INSTAL.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

:: --- Cari python env maganghub ---------------------------------------
set "PYTHON_EXE="
call "%~dp0_common.bat" :cari_python 2>nul
if not defined PYTHON_EXE (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
    echo.
    echo [MASALAH] Python tidak ditemukan.
    echo           Jalankan SETUP_INSTAL.bat terlebih dahulu.
    echo.
    pause
    exit /b 1
)

echo ======================================================================
echo                       LOGIN MAGANGHUB
echo ======================================================================
echo.
echo  Browser Chrome akan terbuka. Lakukan login seperti biasa.
echo  Setelah halaman dashboard MagangHub terbuka, tutup jendela browser.
echo  Sesi akan tersimpan otomatis di file token.json.
echo.
echo  Jendela ini akan menunggu sampai proses login selesai.
echo.
pause

"!PYTHON_EXE!" "login_browser.py"
set "EXIT_CODE=!ERRORLEVEL!"

echo.
if "!EXIT_CODE!"=="0" (
    echo [SELESAI] Sesi login berhasil diperbarui.
) else (
    echo [GAGAL] Proses login berakhir dengan kode !EXIT_CODE!.
    echo         Periksa pesan di atas, lalu coba jalankan lagi.
)
echo.
pause
exit /b !EXIT_CODE!
