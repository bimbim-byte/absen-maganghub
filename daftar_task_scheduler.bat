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
echo Menjalankan pengecekan prasyarat...
echo ----------------------------------------------------------------------

:: --- Pengecekan prasyarat sebelum mendaftar ---------------------------
set "SIAP=1"

if not exist "%~dp0run_hidden.vbs" (
    echo [GAGAL] run_hidden.vbs tidak ditemukan.
    set "SIAP=0"
)
if not exist "%~dp0task1_isi_otomatis.bat" (
    echo [GAGAL] task1_isi_otomatis.bat tidak ditemukan.
    set "SIAP=0"
)
if not exist "%~dp0task2_cek_presensi.bat" (
    echo [GAGAL] task2_cek_presensi.bat tidak ditemukan.
    set "SIAP=0"
)
if not exist "%~dp0task3_ambil_log.bat" (
    echo [GAGAL] task3_ambil_log.bat tidak ditemukan.
    set "SIAP=0"
)
if not exist "%~dp0_common.bat" (
    echo [GAGAL] _common.bat tidak ditemukan.
    set "SIAP=0"
)
if not exist "%~dp0.env" (
    echo [PERINGATAN] File .env belum ada.
    echo              Jalankan SETUP_INSTAL.bat terlebih dahulu agar tugas
    echo              terjadwal tidak langsung gagal saat dijalankan.
)

if "!SIAP!"=="0" (
    echo.
    echo [MASALAH] Sebagian berkas wajib tidak ditemukan.
    echo           Pastikan seluruh berkas aplikasi berada di folder yang sama.
    echo.
    pause
    exit /b 1
)

echo        Semua berkas wajib tersedia.
echo.
echo Mendaftarkan task...
echo ----------------------------------------------------------------------

:: Task 1: Isi Otomatis (Daily 22:00)
schtasks /create /tn "MagangHub_1_IsiOtomatis" /tr "wscript.exe \"%~dp0run_hidden.vbs\" \"%~dp0task1_isi_otomatis.bat\"" /sc DAILY /st 22:00 /f >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Task 1: Isi Otomatis 22:00 berhasil didaftarkan.
) else (
    echo [GAGAL] Gagal mendaftarkan Task 1. Coba jalankan sebagai Administrator.
)

:: Task 2: Cek Presensi & Notifikasi (Setiap 30 Menit)
schtasks /create /tn "MagangHub_2_CekPresensi" /tr "wscript.exe \"%~dp0run_hidden.vbs\" \"%~dp0task2_cek_presensi.bat\"" /sc MINUTE /mo 30 /f >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Task 2: Cek Presensi tiap 30 Menit berhasil didaftarkan.
) else (
    echo [GAGAL] Gagal mendaftarkan Task 2. Coba jalankan sebagai Administrator.
)

:: Task 3: Ambil Data Log Historis (Mingguan - Hari Minggu jam 23:00)
schtasks /create /tn "MagangHub_3_AmbilDataLog" /tr "wscript.exe \"%~dp0run_hidden.vbs\" \"%~dp0task3_ambil_log.bat\"" /sc WEEKLY /d SUN /st 23:00 /f >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] Task 3: Ambil Data Log Mingguan berhasil didaftarkan.
) else (
    echo [GAGAL] Gagal mendaftarkan Task 3. Coba jalankan sebagai Administrator.
)

echo ----------------------------------------------------------------------
echo Pendaftaran selesai. Anda dapat memeriksa hasilnya di Task Scheduler
echo (jalankan: taskschd.msc).
echo.
echo Log eksekusi tiap task tercatat di file .log di folder ini:
echo   task1_isi_otomatis.log
echo   task2_cek_presensi.log
echo   task3_ambil_log.log
echo.
echo Untuk menguji tanpa menunggu jadwal, jalankan file .bat-nya langsung.
echo Untuk menghapus semua task, jalankan:
echo   schtasks /delete /tn "MagangHub_1_IsiOtomatis" /f
echo   schtasks /delete /tn "MagangHub_2_CekPresensi" /f
echo   schtasks /delete /tn "MagangHub_3_AmbilDataLog" /f
echo.
pause
endlocal
