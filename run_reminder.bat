@echo off
setlocal enabledelayedexpansion

:: =========================================================================
:: JIKA PERLU: Anda bisa mengisi path python environment maganghub secara manual
:: di bawah ini jika terpasang di folder kustom (contoh: D:\miniconda3\...)
:: =========================================================================
set "MANUAL_PYTHON="
:: =========================================================================

:: Pindah ke folder skrip saat ini
cd /d "%~dp0"

echo ======================================================
echo [%DATE% %TIME%] Menjalankan Absen Reminder Kemnaker...
echo ======================================================

set "ACTIVATE_PATH="
set "PYTHON_PATH="

:: 0. Prioritaskan jika user mengisi MANUAL_PYTHON
if defined MANUAL_PYTHON (
    if exist "%MANUAL_PYTHON%" (
        set "PYTHON_PATH=%MANUAL_PYTHON%"
        goto :run_python
    )
)

:: 1. Deteksi otomatis dari daftar environment Conda (%USERPROFILE%\.conda\environments.txt)
if exist "%USERPROFILE%\.conda\environments.txt" (
    for /f "usebackq delims=" %%A in ("%USERPROFILE%\.conda\environments.txt") do (
        set "ENV_LINE=%%A"
        echo !ENV_LINE! | findstr /i "maganghub" >nul
        if not errorlevel 1 (
            if exist "!ENV_LINE!\python.exe" (
                set "PYTHON_PATH=!ENV_LINE!\python.exe"
            )
        )
        if exist "!ENV_LINE!\Scripts\activate.bat" (
            if not defined ACTIVATE_PATH set "ACTIVATE_PATH=!ENV_LINE!\Scripts\activate.bat"
        )
    )
)

:: 2. Cari activate.bat di berbagai folder instalasi standar Miniconda / Anaconda
if not defined ACTIVATE_PATH (
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
    ) do (
        if not defined ACTIVATE_PATH (
            if exist "%%~P" set "ACTIVATE_PATH=%%~P"
        )
    )
)

:: 3. Cari python.exe maganghub di folder envs standar
if not defined PYTHON_PATH (
    for %%P in (
        "%USERPROFILE%\.conda\envs\maganghub\python.exe"
        "%USERPROFILE%\miniconda3\envs\maganghub\python.exe"
        "%USERPROFILE%\Miniconda3\envs\maganghub\python.exe"
        "%LOCALAPPDATA%\miniconda3\envs\maganghub\python.exe"
        "%LOCALAPPDATA%\Programs\miniconda3\envs\maganghub\python.exe"
        "C:\miniconda3\envs\maganghub\python.exe"
        "C:\ProgramData\miniconda3\envs\maganghub\python.exe"
        "%USERPROFILE%\anaconda3\envs\maganghub\python.exe"
        "%USERPROFILE%\Anaconda3\envs\maganghub\python.exe"
        "%LOCALAPPDATA%\anaconda3\envs\maganghub\python.exe"
        "C:\anaconda3\envs\maganghub\python.exe"
        "C:\ProgramData\anaconda3\envs\maganghub\python.exe"
        "D:\miniconda3\envs\maganghub\python.exe"
        "E:\miniconda3\envs\maganghub\python.exe"
    ) do (
        if not defined PYTHON_PATH (
            if exist "%%~P" set "PYTHON_PATH=%%~P"
        )
    )
)

:: 4. Cek via perintah 'where conda'
if not defined ACTIVATE_PATH (
    where conda.bat >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%C in ('where conda.bat') do (
            if exist "%%~dpCactivate.bat" set "ACTIVATE_PATH=%%~dpCactivate.bat"
        )
    )
)

:: =========================================================================
:: EKSEKUSI PROGRAM
:: =========================================================================

:: Opsi A: Jalankan dengan mengaktifkan conda environment
if defined ACTIVATE_PATH (
    echo [INFO] Mengaktifkan conda environment "maganghub"...
    echo [INFO] Activate path: "!ACTIVATE_PATH!"
    call "!ACTIVATE_PATH!" maganghub
    python maganghub_api.py
    goto :finish
)

:: Opsi B: Jalankan langsung via binary Python environment maganghub
:run_python
if defined PYTHON_PATH (
    echo [INFO] Menjalankan script menggunakan:
    echo        "!PYTHON_PATH!"
    "!PYTHON_PATH!" maganghub_api.py
    goto :finish
)

:: Opsi C: Gagal mendeteksi environment (Cegah pemanggilan Microsoft Store alias)
echo.
echo ======================================================================
echo [ERROR] Environment Miniconda "maganghub" tidak ditemukan otomatis!
echo ======================================================================
echo Windows tidak menemukan python.exe maganghub di folder default.
echo.
echo CARA MENYELESAIKAN:
echo 1. Buka file run_reminder.bat dengan Notepad / Text Editor.
echo 2. Pada baris ke-6, isi lokasi python.exe maganghub Anda, contoh:
echo    set "MANUAL_PYTHON=C:\Users\%USERNAME%\miniconda3\envs\maganghub\python.exe"
echo 3. Simpan dan jalankan kembali file ini.
echo ======================================================================
echo.
pause
exit /b 1

:finish
echo.
echo [SELESAI] Eksekusi main.py selesai.
:: Jeda 3 detik agar user dapat melihat ringkasan status saat dijalankan manual
timeout /t 3 >nul
endlocal
