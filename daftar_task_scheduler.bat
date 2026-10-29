@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ======================================================================
echo       PENDAFTARAN TASK SCHEDULER MAGANGHUB AUTOMATION
echo ======================================================================
echo.
echo Direktori kerja: %~dp0
echo.
echo Task yang akan dibuat:
echo 1. MagangHub_1_IsiOtomatis   : Setiap hari pukul 22:00
echo 2. MagangHub_2_CekPresensi   : Setiap hari setiap 30 menit
echo 3. MagangHub_3_AmbilDataLog  : Setiap minggu - Minggu pukul 23:00
echo.
echo Menjalankan pendaftaran...
echo ----------------------------------------------------------------------

:: Task 1: Isi Otomatis (Daily 22:00)
schtasks /create /tn "MagangHub_1_IsiOtomatis" /tr "wscript.exe \"%~dp0run_hidden.vbs\" \"%~dp0task1_isi_otomatis.bat\"" /sc DAILY /st 22:00 /f
if %ERRORLEVEL% equ 0 (
    echo [OK] Task 1: Isi Otomatis 22:00 berhasil didaftarkan.
) else (
    echo [GAGAL] Gagal mendaftarkan Task 1.
)

:: Task 2: Cek Presensi & Notifikasi (Setiap 30 Menit)
schtasks /create /tn "MagangHub_2_CekPresensi" /tr "wscript.exe \"%~dp0run_hidden.vbs\" \"%~dp0task2_cek_presensi.bat\"" /sc MINUTE /mo 30 /f
if %ERRORLEVEL% equ 0 (
    echo [OK] Task 2: Cek Presensi tiap 30 Menit berhasil didaftarkan.
) else (
    echo [GAGAL] Gagal mendaftarkan Task 2.
)

:: Task 3: Ambil Data Log Historis (Mingguan - Hari Minggu jam 23:00)
schtasks /create /tn "MagangHub_3_AmbilDataLog" /tr "wscript.exe \"%~dp0run_hidden.vbs\" \"%~dp0task3_ambil_log.bat\"" /sc WEEKLY /d SUN /st 23:00 /f
if %ERRORLEVEL% equ 0 (
    echo [OK] Task 3: Ambil Data Log Mingguan berhasil didaftarkan.
) else (
    echo [GAGAL] Gagal mendaftarkan Task 3.
)

echo ----------------------------------------------------------------------
echo Pendaftaran selesai! Anda dapat memeriksa hasilnya di Task Scheduler (taskschd.msc).
echo Log eksekusi masing-masing task akan otomatis tercatat di file .log di folder ini.
echo.
pause
