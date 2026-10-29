@echo off
setlocal enabledelayedexpansion
title Setup Otomatis - Absen MagangHub
cd /d "%~dp0"

set "ENV_NAME=maganghub"
set "PY_VER=3.11"

cls
echo ======================================================================
echo          SETUP OTOMATIS - ABSEN MAGANGHUB AUTOMATION
echo ======================================================================
echo.
echo  Skrip ini menyiapkan komputer Anda agar aplikasi bisa dipakai.
echo  Yang akan dilakukan:
echo    1. Mencari Miniconda / Anaconda
echo    2. Membuat environment "%ENV_NAME%"
echo    3. Memasang paket Python yang dibutuhkan
echo    4. Memasang browser untuk login
echo    5. Menyiapkan file pengaturan dan folder kerja
echo.
echo  Butuh koneksi internet. Perkiraan waktu: 5 sampai 15 menit.
echo  Jendela ini JANGAN ditutup selama proses berjalan.
echo.
pause
echo.

if not exist "requirements.txt" (
    echo [GAGAL] File requirements.txt tidak ditemukan di folder ini.
    echo         Pastikan SETUP_INSTAL.bat berada di folder yang sama
    echo         dengan file-file aplikasi MagangHub.
    echo.
    pause
    exit /b 1
)

echo [1/7] Mencari Miniconda / Anaconda...
echo ----------------------------------------------------------------------

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
    echo [GAGAL] Miniconda / Anaconda tidak ditemukan di komputer ini.
    echo.
    echo CARA MEMPERBAIKI:
    echo   1. Unduh Miniconda dari: https://docs.conda.io/en/latest/miniconda.html
    echo   2. Pasang dengan pengaturan bawaan, lalu tutup jendela ini.
    echo   3. Jalankan SETUP_INSTAL.bat sekali lagi.
    echo.
    pause
    exit /b 1
)

echo        Ditemukan: "!ACTIVATE_BAT!"
echo.

echo [2/7] Mengaktifkan Conda...
echo ----------------------------------------------------------------------

call "!ACTIVATE_BAT!" base
if errorlevel 1 call "!ACTIVATE_BAT!"

where conda >nul 2>&1
if errorlevel 1 (
    echo.
    echo [GAGAL] Perintah conda tidak dapat dijalankan.
    echo         Coba pasang ulang Miniconda, lalu jalankan skrip ini lagi.
    echo.
    pause
    exit /b 1
)
echo        Conda siap dipakai.
echo.

echo [3/7] Menyiapkan environment "%ENV_NAME%"...
echo ----------------------------------------------------------------------

set "ENV_EXISTS=0"
call "!ACTIVATE_BAT!" %ENV_NAME% >nul 2>&1
if defined CONDA_PREFIX (
    echo !CONDA_PREFIX! | findstr /i /e "\%ENV_NAME%" >nul
    if not errorlevel 1 set "ENV_EXISTS=1"
)

if "!ENV_EXISTS!"=="0" (
    echo        Environment belum ada, membuat baru - mohon tunggu...
    call "!ACTIVATE_BAT!" base >nul 2>&1
    call conda create -y -n %ENV_NAME% python=%PY_VER%
    if errorlevel 1 (
        echo.
        echo [PERINGATAN] Pembuatan environment gagal, mencoba melanjutkan.
    )
    call "!ACTIVATE_BAT!" %ENV_NAME%
) else (
    echo        Environment sudah ada, dipakai kembali.
)

if not defined CONDA_PREFIX (
    echo.
    echo [GAGAL] Environment "%ENV_NAME%" tidak dapat diaktifkan.
    echo.
    pause
    exit /b 1
)

echo %CONDA_PREFIX% | findstr /i /e "\%ENV_NAME%" >nul
if errorlevel 1 (
    echo.
    echo [GAGAL] Environment "%ENV_NAME%" tidak dapat diaktifkan.
    echo         Lokasi aktif saat ini: %CONDA_PREFIX%
    echo.
    pause
    exit /b 1
)

echo        Aktif di: %CONDA_PREFIX%
echo.

echo [4/7] Memasang paket Python...
echo ----------------------------------------------------------------------
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [GAGAL] Pemasangan paket gagal.
    echo         Periksa koneksi internet, lalu jalankan skrip ini lagi.
    echo.
    pause
    exit /b 1
)
echo.

echo [5/7] Memasang browser untuk login...
echo ----------------------------------------------------------------------
python -m playwright install chromium
if errorlevel 1 echo        [PERINGATAN] Chromium Playwright gagal dipasang.

python -m playwright install chrome
if errorlevel 1 (
    echo        [PERINGATAN] Google Chrome tidak dapat dipasang otomatis.
    echo                    Pasang manual dari https://www.google.com/chrome/
)
echo.

echo [6/7] Menyiapkan file pengaturan dan folder kerja...
echo ----------------------------------------------------------------------

if exist ".env" (
    echo        File .env sudah ada, tidak diubah.
) else (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo        File .env dibuat dari .env.example.
    ) else (
        echo        [PERINGATAN] .env.example tidak ditemukan.
    )
)

if not exist "notes" mkdir "notes"
if not exist "drafts" mkdir "drafts"
echo        Folder notes dan drafts siap.
echo.

echo [7/7] Menguji hasil pemasangan...
echo ----------------------------------------------------------------------
python -c "import requests, pytz, dotenv, playwright" >nul 2>&1
if errorlevel 1 (
    echo        [GAGAL] Sebagian paket belum terpasang sempurna.
    echo.
    pause
    exit /b 1
) else (
    echo        Paket inti OK.
)

python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo        [PERINGATAN] tkinter tidak tersedia. Aplikasi jendela tidak bisa dibuka.
) else (
    echo        Tampilan aplikasi OK.
)
echo.

echo ======================================================================
echo                        SETUP SELESAI
echo ======================================================================
echo.
echo  Langkah berikutnya, lakukan berurutan:
echo.
echo    1. Jalankan LOGIN_MAGANGHUB.bat
echo       Browser akan terbuka. Login seperti biasa.
echo       Setelah masuk dashboard, tutup jendela browser.
echo.
echo    2. Jalankan buka_aplikasi.bat
echo       Tulis catatan aktivitas, tekan Generate via Gemini,
echo       lalu tekan Kirim Laporan Harian MagangHub.
echo.
echo  Opsional:
echo    - Isi GEMINI_API_KEY di file .env agar AI bisa menulis otomatis.
echo    - Jalankan daftar_task_scheduler.bat agar laporan terisi otomatis.
echo.
echo  Panduan lengkap: buka file PANDUAN_PENGGUNA.md
echo.
pause
endlocal
