# Absen MagangHub Automation

## Ringkasan
Repository ini mengotomatisasi absensi harian untuk **MagangHub Kemnaker** menggunakan Playwright. Skrip akan login ke portal, mengambil token sesi, dan dapat mengirim notifikasi ringkas melalui Telegram.

## Prasyarat
1. **Python 3.9+** (skrip ditulis untuk Python 3).<br>
2. **Miniconda / Anaconda** (opsional) – Anda dapat menggunakan lingkungan Python apa saja asalkan paket yang diperlukan terpasang.
3. **Git** – untuk meng‑clone repositori.

## Catatan `.gitignore`
File `.gitignore` telah ditambahkan entri untuk mengabaikan direktori sementara Playwright (`chrome_session/`) serta folder `Galaxies/` dan file lain yang tidak perlu di‑track.

## Cara Cepat Memulai
```bash
# 1. Clone repositori
git clone https://github.com/bimbim-byte/absen-maganghub.git
cd absen_maganghub

# 2. Buat lingkungan virtual (disarankan)
conda create -n xmypro python=3.9 -y
conda activate xmypro

# 3. Instal dependensi
pip install -r requirements.txt

# 4. Siapkan variabel lingkungan
cp .env.example .env   # salin template
# Edit .env dan isi nilai yang diperlukan (API key, username, password, dll.)

# 5. Jalankan skrip utama
python main.py
```
# 6. (Optional) Jalankan Sejenis Task Scheduler / Trigger 
Jika menggunakan windows, buat file .bat kemudian setting Task Scheduler agar cookie selalu terjaga, serta notifikasi dapat selalu dikirimkan

Skrip akan:
- Memuat kredensial dari **.env**.
- Menggunakan **interpreter Python yang sedang menjalankan `main.py`** (`sys.executable`). Pastikan Playwright terinstal di lingkungan tersebut.
- Jika token akses kedaluwarsa, secara otomatis membuka browser Playwright untuk login ulang.
- Opsional mengirim notifikasi singkat ke Telegram.

## Variabel Lingkungan (`.env`)

Salin baris berikut ke `.env` Anda:

```dotenv
# Notifikasi Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Jam operasional pengecekan (format 24 jam)
START_HOUR=1
END_HOUR=23

# Jumlah item per halaman saat memanggil API
LIMIT=100

# Endpoint & header WAF (jarang perlu diubah)
MONEV_API_BASE=https://monev-api.maganghub.kemnaker.go.id/api/v1
FRONTEND_BUILD_ID=0e35fee4027705f4f5a18734d390979873c42ddd-production

# Rentang bulan untuk collect_activity.py (WAJIB diisi user)
# Format: YYYY-MM
MULAI_BULAN=2026-10
AKHIR_BULAN=2026-12
```

| Variabel | Wajib | Deskripsi |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ya | Token bot Telegram untuk notifikasi |
| `TELEGRAM_CHAT_ID` | ya | ID chat tujuan pengiriman pesan |
| `START_HOUR` / `END_HOUR` | tidak | Jam operasional pengecekan (default 1 dan 23) |
| `LIMIT` | tidak | Jumlah item per halaman API (default 100) |
| `MONEV_API_BASE` | tidak | Base URL API MONEV |
| `FRONTEND_BUILD_ID` | tidak | Header `x-frontend-build-id`; perbarui bila API menolak request |
| `MULAI_BULAN` | ya (khusus collector) | Bulan awal pengambilan data, format `YYYY-MM` |
| `AKHIR_BULAN` | ya (khusus collector) | Bulan akhir pengambilan data, format `YYYY-MM` |

> Catatan: `USERNAME`, `PASSWORD`, `TOKEN`, dan `MONEV_REFRESH_TOKEN` **tidak** dibaca dari `.env`.
> Login sepenuhnya manual di browser (`get_cookie.py`), dan token disimpan di `token.json`.

### Generate daily log via Gemini (`generate_log.py`)

Tambahkan dua variabel berikut ke `.env`:

```dotenv
GEMINI_API_KEY=isi_api_key_anda
GEMINI_MODEL=gemini-2.0-flash
```

Alur kerja:

```powershell
# 1. Kumpulkan korpus historis (butuh MULAI_BULAN/AKHIR_BULAN)
conda run -n maganghub python collect_activity.py

# 2. Preview dulu — TIDAK mengirim apa pun ke server
conda run -n maganghub python generate_log.py "mempelajari disassembly printer dot matrix, backup image windows"

# 3. Kirim setelah draft sesuai
conda run -n maganghub python generate_log.py "..." --date 2026-10-20 --submit
```

Tanpa `--submit`, skrip hanya menulis `generated_log.json` dan menampilkan preview.

| Flag | Fungsi |
|---|---|
| `--date YYYY-MM-DD` | Tanggal target (default: hari ini WIB) |
| `--submit` | Kirim ke `POST /attendances/with-daily-log` |
| `--examples N` | Jumlah contoh few-shot dari korpus (default 6) |

Status absensi di-hardcode `PRESENT` di `build_payload()`. Ubah bila perlu `SICK`/`LEAVE`/`ABSENT`.

> `FRONTEND_BUILD_ID` perlu diperbarui bila server membalas 403. Nilai di header
> bisa berubah sewaktu-waktu; salin ulang dari DevTools tab Network.

### Aturan rentang bulan

`collect_activity.py` mengambil data dari **tanggal 1 `MULAI_BULAN`** sampai **hari terakhir `AKHIR_BULAN`**, dengan pemotongan otomatis:

- Jika `AKHIR_BULAN` melewati bulan berjalan, otomatis dipotong ke bulan berjalan.
- Jika `AKHIR_BULAN` adalah bulan berjalan, dipotong lagi sampai **hari ini** (tanggal masa depan tidak akan pernah punya log).
- Jika `MULAI_BULAN` lebih besar dari batas akhir, tidak ada data yang diambil.

Contoh: hari ini `2026-10-23`, dengan `MULAI_BULAN=2026-08` dan `AKHIR_BULAN=2026-12`,
maka rentang efektif adalah **2026-08-01 s/d 2026-10-23**.

## Cara Pemilihan Interpreter
Tidak ada lagi path Conda yang hard‑coded. Skrip cukup memakai **interpreter Python yang menjalankan `main.py`** (`sys.executable`). Pastikan Playwright terpasang di lingkungan tersebut:
```bash
pip install playwright
playwright install
```
Jika Anda menjalankan skrip dari lingkungan lain, interpreter tersebut akan otomatis dipakai.

## Kontribusi
1. Fork repositori.
2. Buat cabang fitur.
3. Lakukan perubahan.
4. Jika menambah variabel rahasia, perbarui `.env.example`.
5. Ajukan pull request.
