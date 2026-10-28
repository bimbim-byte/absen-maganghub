# Absen MagangHub Automation

Alat bantu mengisi **laporan harian (daily log)** di MagangHub Kemnaker.
Anda menulis catatan singkat, Gemini mengembangkannya menjadi laporan lengkap, lalu Anda kirim.

> **Telegram dan Gemini bersifat opsional.** Tanpa keduanya sistem tetap berjalan.

---

## Yang Bisa Anda Jalankan

Hanya **empat** file yang perlu Anda jalankan sendiri. Dua sisanya bekerja di belakang layar.

| Perintah | Fungsi | Wajib? |
|---|---|---|
| `python login_browser.py` | Buka browser untuk login, simpan sesi ke `token.json` | Ya, saat pertama dan bila sesi habis |
| `python 2_aplikasi_isi_laporan.py` | **Aplikasi utama** — tulis catatan, Gemini isi otomatis, kirim | Ya, dipakai harian |
| `python 1_ambil_data_log.py` | Ambil riwayat log lama sebagai contoh gaya | Opsional |
| `python 3_isi_otomatis.py` | Isi laporan otomatis lewat penjadwal | Opsional |

**Dua file yang tidak dijalankan langsung:**

| File | Fungsi |
|---|---|
| `maganghub_api.py` | Lapisan API: header, refresh token, kirim request, notifikasi |
| `gemini_helper.py` | Integrasi Gemini dan fungsi pengiriman (dipakai file di atas) |

> Penomoran `1_`, `2_`, `3_` menunjukkan urutan pemakaian, bukan urutan wajib.

---

## Yang Wajib vs Opsional

Sistem berfungsi **tanpa** Telegram dan **tanpa** Gemini. Fitur yang tidak diisi akan dilewati otomatis.

| Fitur | Butuh apa | Bila tidak diisi |
|---|---|---|
| Ambil data dan kirim laporan | Login browser saja | — |
| Generate otomatis (AI) | `GEMINI_API_KEY` | Anda mengisi ketiga field manual di aplikasi |
| Notifikasi | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Tidak ada notifikasi, sisanya tetap jalan |

Artinya: **minimal cukup login lalu isi manual.** Gemini mempermudah, Telegram tidak wajib sama sekali.

---

## Cara Cepat Memulai

```bash
# 1. Clone repositori
git clone https://github.com/bimbim-byte/absen-maganghub.git
cd absen-maganghub

# 2. Buat lingkungan (disarankan)
conda create -n maganghub python=3.11 -y
conda activate maganghub

# 3. Instal dependensi
pip install -r requirements.txt
playwright install

# 4. Salin template konfigurasi
copy .env.example .env    # Windows
cp .env.example .env      # Linux/Mac

# 5. Login sekali (browser akan terbuka, login manual)
python login_browser.py

# 6. Buka aplikasi
python 2_aplikasi_isi_laporan.py
```

Setelah langkah 5 berhasil, `token.json` terisi dan sesi bertahan beberapa hari.

---

## Variabel `.env`

Hanya bagian **Wajib** yang harus diisi.

```dotenv
# ============ WAJIB ============
# Rentang bulan untuk 1_ambil_data_log.py (format YYYY-MM)
MULAI_BULAN=2026-08
AKHIR_BULAN=2026-12

# ============ OPSIONAL: Gemini ============
# Ambil di https://aistudio.google.com/apikey
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# ============ OPSIONAL: Telegram ============
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# ============ JARANG DIUBAH ============
LIMIT=100
START_HOUR=1
END_HOUR=23
FILL_HOUR=22
MONEV_API_BASE=https://monev-api.maganghub.kemnaker.go.id/api/v1
FRONTEND_BUILD_ID=19caeeb678c107906cf943cdfb383397fe90fc24-production
```

| Variabel | Status | Keterangan |
|---|---|---|
| `MULAI_BULAN` / `AKHIR_BULAN` | **Wajib** | Rentang bulan pengambilan data, format `YYYY-MM` |
| `GEMINI_API_KEY` | Opsional | Tanpa ini AI tidak aktif, isi laporan manual |
| `GEMINI_MODEL` | Opsional | Model Gemini yang dipakai |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Opsional | Tanpa ini tidak ada notifikasi |
| `LIMIT` | Opsional | Item per halaman API (default 100) |
| `MONEV_API_BASE` | Opsional | Base URL API |
| `FRONTEND_BUILD_ID` | Opsional | Perbarui bila server membalas **403** |
| `START_HOUR` / `END_HOUR` | Opsional | Jam operasional pengecekan laporan |
| `FILL_HOUR` | Opsional | Batas jam minimal `3_isi_otomatis.py` (default 22) |

> `USERNAME`, `PASSWORD`, `TOKEN`, dan `MONEV_REFRESH_TOKEN` **tidak** dibaca dari `.env`.
> Login sepenuhnya manual lewat `login_browser.py`, sesi disimpan di `token.json`.

---

## Penjelasan Tiap File

### `login_browser.py` — login dan simpan sesi

Membuka Chromium Playwright. Anda login seperti biasa di browser. Setelah berhasil, cookie dan token disimpan ke `token.json` sehingga skrip lain tidak perlu login ulang.

```bash
python login_browser.py
```

Jalankan lagi bila muncul pesan sesi kedaluwarsa.

### `2_aplikasi_isi_laporan.py` — aplikasi utama

```
+------------------------------------------------+
| Tanggal [2026-10-23]  Status [PRESENT v]       |
+------------------------------------------------+
| Catatan aktivitas (input Anda)                 |
| +--------------------------------------------+ |
| | 07.30 cek server, ganti toner, backup image| |
| +--------------------------------------------+ |
| [Generate via Gemini (Ctrl+Enter)] [Bersihkan] |
+------------------------------------------------+
| Aktivitas Harian    (hasil AI, boleh diedit)   |
| Pelajaran yang Didapat                         |
| Kendala                                        |
+------------------------------------------------+
| Berhasil! Laporan sudah terkirim.              |
| [Simpan Draft] [Kirim Laporan Harian MagangHub]|
+------------------------------------------------+
```

Alurnya:

1. Isi kotak **Catatan aktivitas** dengan poin-poin kasar
2. Tekan **Generate via Gemini** — tiga kotak bawah terisi otomatis
3. Periksa dan edit bila ada yang kurang tepat
4. Tekan **Kirim Laporan Harian MagangHub**
5. Banner hijau atau merah muncul menandakan berhasil atau gagal

Bila `GEMINI_API_KEY` kosong, langkah 2 menampilkan peringatan — Anda tetap bisa mengisi ketiga kotak secara manual.

```bash
python 2_aplikasi_isi_laporan.py
```

### `1_ambil_data_log.py` — ambil contoh gaya tulisan

Mengambil riwayat laporan Anda dan menyimpannya ke `activity_logs.json`. File ini dipakai Gemini sebagai **contoh gaya** agar hasilnya meniru cara Anda menulis.

```bash
python 1_ambil_data_log.py
```

Tanpa langkah ini aplikasi tetap jalan, tetapi hasil Gemini terasa generik. Jalankan sekali, ulangi bila ingin contoh yang lebih baru.

**Aturan rentang** — mengambil dari tanggal 1 `MULAI_BULAN` sampai hari terakhir `AKHIR_BULAN`, dipotong otomatis:

- Bila `AKHIR_BULAN` melewati bulan ini, dipotong ke bulan ini
- Bila `AKHIR_BULAN` adalah bulan ini, dipotong sampai **hari ini**
- Bila `MULAI_BULAN` lebih besar dari batas akhir, tidak ada data diambil

Contoh: hari ini `2026-10-23`, `MULAI_BULAN=2026-08`, `AKHIR_BULAN=2026-12` menghasilkan rentang efektif **2026-08-01 s/d 2026-10-23**.

### `3_isi_otomatis.py` — isi otomatis terjadwal

Mengisi laporan tanpa membuka aplikasi. Membaca catatan dari `notes/YYYY-MM-DD.txt`.

```bash
# Preview, tidak mengirim apa pun
python 3_isi_otomatis.py

# Kirim sungguhan
python 3_isi_otomatis.py --submit

# Untuk kemarin
python 3_isi_otomatis.py --target yesterday --submit
```

**Penting:** bila file catatan tidak ada, skrip **tidak akan mengarang isi**. Ia hanya mengirim pengingat lewat Telegram (jika dikonfigurasi) lalu berhenti.

Membuat catatan:

1. Buat folder `notes/`
2. Buat file `notes/2026-10-23.txt`
3. Isi dengan poin-poin kasar, format bebas

Contoh isi `notes/2026-10-23.txt`:

```text
07.30  Cek server HOM dan AX, restart service yang not responding
08.30  Bersihkan cache poliklinik, cek koneksi ke ruang ranap
10.00  Ganti toner printer di loket pendaftaran
13.00  Backup image Windows PC kasir
```

| Flag | Fungsi |
|---|---|
| `--submit` | Benar-benar mengirim, tanpa ini hanya draft |
| `--target today` atau `--target yesterday` | Tanggal tujuan |
| `--force` | Proses walau laporan sudah ada |
| `--ignore-hour` | Abaikan batas `FILL_HOUR` |

---

## Menjalankan Terjadwal (Windows)

Menggunakan **Task Scheduler** agar `3_isi_otomatis.py` berjalan tiap pagi.

**1. Buat file `auto.bat`:**

```bat
@echo off
cd /d C:\path\ke\absen-maganghub
call conda activate maganghub
python 3_isi_otomatis.py --submit >> auto.log 2>&1
```

**2. Buka Task Scheduler, pilih Create Basic Task**

- Trigger: **Daily**, jam `22:00`
- Action: **Start a program**, pilih `auto.bat`
- Centang **Run whether user is logged on or not**

**3. Uji dulu** dengan menjalankan `auto.bat` manual.

Karena ada guard `FILL_HOUR` (default **22**), skrip aman dijadwalkan lebih awal — ia akan diam bila belum pukul 22:00 WIB. Menjalankan tugas pada 21:00 atau 23:00 sama-sama aman, asalkan setelah batas tersebut.

---

## Pemilihan Interpreter

Tidak ada path Conda yang di-hardcode. Skrip memakai **interpreter Python yang menjalankannya** (`sys.executable`). Pastikan Playwright terpasang di lingkungan tersebut:

```bash
pip install playwright
playwright install
```

---

## Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `Participant ID not found` | Sesi belum ada | `python login_browser.py` |
| HTTP **401** | Sesi kedaluwarsa | `python login_browser.py` |
| HTTP **403** | `FRONTEND_BUILD_ID` usang | Salin nilai terbaru dari DevTools, tab Network |
| HTTP **409** | Laporan tanggal itu sudah ada | Pilih tanggal lain, atau `--force` |
| HTTP **422** | Format data ditolak | Periksa tanggal (`YYYY-MM-DD`) dan status |
| `GEMINI_API_KEY belum diisi` | Variabel kosong | Isi di `.env`, atau gunakan mode manual |
| Gemini HTTP **429** | Kuota habis | Tunggu, atau ganti model ke `gemini-2.0-flash-lite` |
| `Field ... kosong` | Jawaban AI terlalu minimal | Perjelas isi catatan |
| Aplikasi tidak muncul | tkinter bermasalah | `python -c "import tkinter"` |
| Browser tidak terbuka | Playwright belum terpasang | `playwright install` |

**Cara mengambil `FRONTEND_BUILD_ID` terbaru:**

1. Buka MagangHub di browser
2. Tekan `F12`, buka tab **Network**
3. Lakukan aktivitas apa saja hingga muncul request
4. Cari request ke `monev-api`, lihat header `x-frontend-build-id`
5. Salin nilainya ke `.env`

---

## Data yang Disimpan

| File | Isi | Aman di-commit? |
|---|---|---|
| `token.json` | Sesi login | Tidak, sudah di `.gitignore` |
| `activity_logs.json` | Riwayat log Anda | Tidak, sudah di `.gitignore` |
| `generated_log.json` | Draft terakhir | Tidak, sudah di `.gitignore` |
| `notes/` | Catatan harian | Tidak, sudah di `.gitignore` |
| `drafts/` | Draft otomatis | Tidak, sudah di `.gitignore` |

---

## Kontribusi

1. Fork repositori
2. Buat cabang fitur
3. Lakukan perubahan
4. Perbarui `.env.example` bila menambah variabel baru
5. Ajukan pull request