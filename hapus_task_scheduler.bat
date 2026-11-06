@echo off
:: ======================================================================
:: hapus_task_scheduler.bat - Hapus semua task terjadwal MagangHub
:: ======================================================================
setlocal enabledelayedexpansion
title Hapus Task Scheduler MagangHub
cd /d "%~dp0"

echo ======================================================================
echo            HAPUS TASK SCHEDULER MAGANGHUB AUTOMATION
echo ======================================================================
echo.
echo Task berikut akan dihapus:
echo   1. MagangHub_1_IsiOtomatis
echo   2. MagangHub_2_CekPresensi
echo   3. MagangHub_3_AmbilDataLog
echo.
echo Pengisian otomatis akan berhenti sampai Anda menjalankan
echo daftar_task_scheduler.bat lagi.
echo.
set /p "KONFIRMASI=Lanjutkan hapus? (y/n): "
if /i not "!KONFIRMASI!"=="y" (
    echo Dibatalkan. Tidak ada yang diubah.
    echo.
    pause
    exit /b 0
)

echo.
echo ----------------------------------------------------------------------
set "GAGAL=0"

schtasks /delete /tn "MagangHub_1_IsiOtomatis" /f >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Task 1 dihapus.
) else (
    echo [INFO] Task 1 tidak ditemukan atau gagal dihapus.
    set "GAGAL=1"
)

schtasks /delete /tn "MagangHub_2_CekPresensi" /f >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Task 2 dihapus.
) else (
    echo [INFO] Task 2 tidak ditemukan atau gagal dihapus.
    set "GAGAL=1"
)

schtasks /delete /tn "MagangHub_3_AmbilDataLog" /f >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Task 3 dihapus.
) else (
    echo [INFO] Task 3 tidak ditemukan atau gagal dihapus.
    set "GAGAL=1"
)

echo ----------------------------------------------------------------------
echo.
if "!GAGAL!"=="0" (
    echo Selesai. Semua task terjadwal telah dihapus.
) else (
    echo Selesai. Sebagian task mungkin belum pernah didaftarkan.
    echo Bila tombol gagal dihapus, jalankan skrip ini sebagai Administrator.
)
echo.
pause
endlocal
