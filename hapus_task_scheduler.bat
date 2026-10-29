@echo off
setlocal

echo ======================================================================
echo       PENGHAPUSAN TASK SCHEDULER MAGANGHUB AUTOMATION
echo ======================================================================
echo.
echo Menghapus task dari Windows Task Scheduler...
echo.

schtasks /delete /tn "MagangHub_1_IsiOtomatis" /f >nul 2>&1
echo [OK] Task 1 (MagangHub_1_IsiOtomatis) dihapus.

schtasks /delete /tn "MagangHub_2_CekPresensi" /f >nul 2>&1
echo [OK] Task 2 (MagangHub_2_CekPresensi) dihapus.

schtasks /delete /tn "MagangHub_3_AmbilDataLog" /f >nul 2>&1
echo [OK] Task 3 (MagangHub_3_AmbilDataLog) dihapus.

echo.
echo Semua task MagangHub telah dihapus.
echo.
pause

