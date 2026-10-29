# Absen MagangHub Kemnaker Automation

Aplikasi asisten dan otomatisasi pengisian **Laporan Harian (Daily Log)** dan presensi untuk peserta program MagangHub Kementerian Ketenagakerjaan (Kemnaker) Republik Indonesia.

Aplikasi ini mengubah catatan aktivitas harian yang ringkas menjadi laporan kerja formal dan terstruktur secara instan menggunakan bantuan model AI (Google Gemini), lalu mengirimkannya langsung ke sistem MagangHub Kemnaker melalui antarmuka API resmi.

---

## 🛡️ Jaminan Keamanan & Privasi (Security & Privacy First)

Aplikasi ini dirancang dengan prinsip **Local-First & Zero-Intermediary** untuk memastikan keamanan dan kerahasiaan akun Anda:

* **Tanpa Server Pihak Ketiga (No Third-Party Backend)**: Tidak ada server perantara, basis data daring, atau analitik yang dioperasikan oleh pengembang. Seluruh eksekusi berjalan 100% di komputer lokal Anda.
* **Koneksi Langsung & Terverifikasi**:
  * Seluruh data absensi dan laporan dikirim langsung ke endpoint resmi Kemnaker: `https://monev-api.maganghub.kemnaker.go.id/api/v1`.
  * Pemrosesan teks laporan hanya dikirim langsung ke Google Gemini API (`https://generativelanguage.googleapis.com`) menggunakan API Key pribadi pengguna.
  * Notifikasi bot dikirim langsung ke server Telegram (`https://api.telegram.org`).
* **Kredensial Akun Aman**: Kata sandi (*password*) Anda tidak pernah dibaca, disimpan, atau dicatat oleh aplikasi. Login dilakukan melalui browser Google Chrome resmi via Playwright, dan sesi disimpan secara lokal di file [**`token.json`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/token.json).
* **Kode Sumber Terbuka & Transparan**: Setiap baris skrip Python dan file Batch terbuka untuk diaudit dan ditinjau secara bebas.
* **Perlindungan Repositori Bawaan**: File sensitif seperti `.env`, `token.json`, `activity_logs.json`, folder catatan `notes/`, dan draft `drafts/` secara baku telah didaftarkan pada [**`.gitignore`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/.gitignore) untuk mencegah kebocoran data pribadi ke repositori publik.

---

## ✨ Fitur Utama

* **Desktop GUI App (Tkinter)**: Tampilan visual yang bersih, ringan, dan responsif. Mendukung tombol pintas `Ctrl+Enter` untuk generate laporan secara cepat.
* **Few-Shot Learning Gemini AI**: AI tidak hanya mengarang, tetapi dilatih meniru gaya bahasa, kedalaman teknis, dan struktur laporan historis Anda sendiri dari log masa lalu.
* **Smart Auto-Recovery Sesi (HTTP 401)**: Jika masa aktif access token habis, sistem otomatis melakukan pembaruan (*refresh token*) di latar belakang tanpa mengganggu alur kerja pengguna.
* **Pengisian Otomatis Terjadwal**: Tersedia skrip headless yang dapat diintegrasikan dengan Windows Task Scheduler untuk mengisi laporan otomatis pada pukul 22:00 WIB dari file catatan harian (`notes/YYYY-MM-DD.txt`).
* **Proteksi Hari Libur**: Otomatis mendeteksi hari libur nasional resmi Kemnaker dan hari libur mingguan profil peserta agar tidak mengirimkan laporan pada hari non-kerja.
* **Notifikasi Telegram**: Memberikan pengingat absensi, konfirmasi keberhasilan pengiriman laporan, dan peringatan jika sesi login kedaluwarsa.

---

## 📁 Struktur Berkas

```text
absen-maganghub/
├── 2_aplikasi_isi_laporan.py    # Aplikasi GUI Desktop utama (Tkinter)
├── login_browser.py             # Penangan login SSO & penyimpan sesi Playwright
├── maganghub_api.py             # Driver API MagangHub, token recovery & Telegram
├── gemini_helper.py             # Modul integrasi Google Gemini AI & submit payload
├── 1_ambil_data_log.py          # Pengekstrak log historis untuk basis few-shot AI
├── 3_isi_otomatis.py            # Skrip pengisian otomatis berbasis CLI/jadwal
│
├── SETUP_INSTAL.bat             # Skrip instalasi & penyiapan Conda otomatis
├── buka_aplikasi.bat            # Launcher GUI Desktop tanpa konsol hitam
├── LOGIN_MAGANGHUB.bat          # Launcher perpanjangan sesi login di browser
├── daftar_task_scheduler.bat    # Pendaftar tugas otomatis ke Windows Task Scheduler
├── hapus_task_scheduler.bat     # Penghapus tugas terjadwal dari Windows
├── task1_isi_otomatis.bat       # Wrapper task scheduler: pengisian harian
├── task2_cek_presensi.bat       # Wrapper task scheduler: cek presensi berkala
├── task3_ambil_log.bat          # Wrapper task scheduler: sinkronisasi log mingguan
├── run_hidden.vbs               # Eksekutor batch background senyap
├── run_reminder.bat             # Skrip diagnostik & pengingat presensi
│
├── requirements.txt             # Dependensi Python pip
├── environment.yml              # Manifes environment Conda standar
├── .env.example                 # Template variabel konfigurasi lingkungan
├── PANDUAN_PENGGUNA.md          # Panduan pemakaian ramah pemula
└── README.md                    # Dokumentasi teknis proyek
```

---

## 🚀 Panduan Pemasangan

Pastikan komputer telah terpasang **Miniconda** ([Unduh di sini](https://docs.conda.io/en/latest/miniconda.html)) dan **Google Chrome**.

### Opsi A: Menggunakan Batch Setup (Sangat Direkomendasikan untuk Windows)
1. Buka folder proyek ini.
2. Klik dua kali file [**`SETUP_INSTAL.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/SETUP_INSTAL.bat).
3. Skrip otomatis mendeteksi Conda, membuat environment `maganghub` (Python 3.11), memasang seluruh pustaka, dan menyiapkan struktur direktori kerja.
4. Selesai saat muncul tulisan **SETUP SELESAI**.

### Opsi B: Pemasangan Manual via CLI / Terminal
Jika Anda terbiasa menggunakan Command Line atau berada di lingkungan non-Windows:

```bash
# 1. Masuk ke folder proyek
cd absen-maganghub

# 2. Buat environment Conda dari berkas environment.yml
conda env create -f environment.yml

# 3. Aktifkan environment
conda activate maganghub

# 4. Pasang browser Playwright
playwright install chromium

# 5. Siapkan konfigurasi .env
copy .env.example .env    # Windows
# cp .env.example .env    # Linux / macOS
```

---

## ⚙️ Konfigurasi Variabel Lingkungan (`.env`)

Buka file `.env` dengan text editor untuk menyesuaikan parameter:

```dotenv
# ============================================================
# WAJIB (Rentang Sinkronisasi Riwayat Laporan)
# ============================================================
MULAI_BULAN=2026-08
AKHIR_BULAN=2026-12

# ============================================================
# FITUR AI: GOOGLE GEMINI (Opsional tetapi Sangat Disarankan)
# Dapatkan gratis di: https://aistudio.google.com/apikey
# ============================================================
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.0-flash

# ============================================================
# NOTIFIKASI TELEGRAM (Opsional)
# ============================================================
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# ============================================================
# PENGATURAN API & SERVER (Jarang Diubah)
# ============================================================
LIMIT=100
START_HOUR=1
END_HOUR=23
FILL_HOUR=22
MONEV_API_BASE=https://monev-api.maganghub.kemnaker.go.id/api/v1
FRONTEND_BUILD_ID=fdce5864ab936c3205233ffc340ba593c0136cd2-production
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36
```

---

## 💻 Alur Penggunaan

### 1. Inisialisasi Sesi Login
Jalankan file [**`LOGIN_MAGANGHUB.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/LOGIN_MAGANGHUB.bat) (atau `python login_browser.py`). Browser Chrome akan terbuka. Lakukan login akun SSO MagangHub seperti biasa. Setelah dashboard terbuka, tutup browser. Token sesi akan tersimpan di `token.json`.

### 2. Pengambilan Basis Gaya Tulisan (Opsional)
Jalankan:
```bash
python 1_ambil_data_log.py
```
Skrip akan mengunduh log lama Anda dan menyimpannya ke `activity_logs.json`. Gemini akan menggunakan data ini sebagai referensi gaya penulisan pribadi Anda.

### 3. Penggunaan Harian via Aplikasi Desktop
Klik dua kali [**`buka_aplikasi.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/buka_aplikasi.bat) (atau `python 2_aplikasi_isi_laporan.py`):
1. Masukkan poin singkat pekerjaan Anda di kotak **Catatan aktivitas**.
2. Tekan **Generate via Gemini (Ctrl+Enter)**.
3. Review hasil teks pada kotak *Aktivitas Harian*, *Pelajaran*, dan *Kendala*.
4. Klik **Kirim Laporan Harian MagangHub**.

### 4. Pengisian Otomatis via Scheduler (Headless)
Untuk mengisi otomatis tanpa membuka GUI:
1. Buat catatan aktivitas di folder `notes/` dengan format nama `YYYY-MM-DD.txt` (contoh: `notes/2026-10-29.txt`).
2. Daftarkan tugas terjadwal dengan menjalankan [**`daftar_task_scheduler.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/daftar_task_scheduler.bat).
3. Setiap malam pukul 22:00 WIB, skrip [**`3_isi_otomatis.py`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/3_isi_otomatis.py) akan memproses catatan tersebut dan mengirimkannya ke server secara mandiri.

---

## 🔍 Panduan Penanganan Masalah (Troubleshooting)

| Respon / Gejala | Diagnosa Masalah | Solusi Perbaikan |
|---|---|---|
| **HTTP 401 Unauthorized** | Sesi login habis / refresh token kedaluwarsa. | Jalankan `LOGIN_MAGANGHUB.bat` untuk memperbarui sesi. |
| **HTTP 403 Forbidden** | Nilai `FRONTEND_BUILD_ID` telah kedaluwarsa karena server MagangHub merilis versi build frontend baru. | Buka MagangHub di browser biasa, tekan `F12` (DevTools) > tab **Network**, temukan request ke `monev-api`, salin header `x-frontend-build-id`, lalu tempelkan ke `.env`. |
| **HTTP 409 Conflict** | Laporan untuk tanggal tersebut sudah tercatat di server. | Pastikan Anda memilih tanggal yang belum diisi, atau gunakan argumen `--force` pada skrip CLI. |
| **HTTP 422 Unprocessable** | Format data tanggal atau status kehadiran tidak valid. | Pastikan format tanggal adalah `YYYY-MM-DD` dan status adalah salah satu dari `PRESENT`, `SICK`, `LEAVE`, atau `ABSENT`. |
| **HTTP 429 Too Many Requests** | Limit kuota permintaan Gemini API terlampaui. | Tunggu beberapa saat, atau ubah `GEMINI_MODEL=gemini-2.0-flash-lite` pada `.env`. |
| **Participant ID not found** | Sesi belum pernah dimuat dari browser. | Pastikan telah menjalankan `LOGIN_MAGANGHUB.bat` hingga masuk halaman dashboard utama. |

---

## 📜 Ketentuan & Tanggung Jawab (Disclaimer)

Aplikasi ini dikembangkan sebagai alat bantu (*productivity tool*) personal bagi peserta magang untuk memudahkan administrasi pelaporan harian secara efisien. Pengguna bertanggung jawab penuh atas keakuratan, kebenaran, dan integritas isi laporan yang dikirimkan ke portal MagangHub Kemnaker.
