# Absen MagangHub Automation

## Ringkasan
Repository ini mengotomatisasi absensi harian untuk **MagangHub Kemnaker** menggunakan Playwright. Skrip akan login ke portal, mengambil token sesi, dan dapat mengirim notifikasi ringkas melalui Telegram.

## Prasyarat
1. **Python 3.9+** (skrip ditulis untuk Python 3).<br>
2. **Miniconda / Anaconda** (opsional) – Anda dapat menggunakan lingkungan Python apa saja asalkan paket yang diperlukan terpasang.
3. **Git** – untuk meng‑clone repositori.

## Cara Cepat Memulai
```bash
# 1. Clone repositori
git clone <YOUR_GITHUB_REPO_URL>
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

Skrip akan:
- Memuat kredensial dari **.env**.
- Menggunakan **interpreter Python yang sedang menjalankan `main.py`** (`sys.executable`). Pastikan Playwright terinstal di lingkungan tersebut.
- Jika token akses kedaluwarsa, secara otomatis membuka browser Playwright untuk login ulang.
- Opsional mengirim notifikasi singkat ke Telegram.

## Variabel Lingkungan (`.env`)
| Variabel | Deskripsi |
|---|---|
| `USERNAME` | Username MagangHub Anda |
| `PASSWORD` | Password MagangHub Anda |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram untuk notifikasi |
| `TELEGRAM_CHAT_ID` | ID chat tujuan pengiriman pesan |
| `TOKEN` | (opsional) Token akses yang sudah ada |
| `MONEV_REFRESH_TOKEN` | (opsional) Refresh token untuk API MONEV |
| `...` | Tambahkan variabel rahasia lain bila diperlukan |

> **Jangan pernah meng‑commit file `.env`**. Repository sudah menambahkan `.env` ke `.gitignore`.

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

## Lisensi
MIT – bebas digunakan dan dimodifikasi.
