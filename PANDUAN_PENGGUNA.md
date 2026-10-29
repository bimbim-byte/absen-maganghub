# Panduan Pengguna — Absen & Laporan MagangHub Kemnaker

Panduan ini disusun untuk siapa saja, termasuk pengguna yang **belum pernah menggunakan Python atau terminal sebelumnya**. Seluruh proses utama dapat dijalankan dengan **klik dua kali** pada file `.bat` yang telah disediakan.

---

## 🛡️ Apakah Aplikasi Ini Aman? (Jaminan Privasi)

Keamanan akun dan data Anda adalah prioritas utama. Aplikasi ini dirancang dengan prinsip **Zero-Server / Local-First**:

1. **100% Berjalan di Komputer Anda Sendiri**: Aplikasi ini tidak memiliki server perantara (*third-party backend*). Semua data tersimpan lokal di laptop/PC Anda.
2. **Koneksi Langsung & Resmi**:
   * Pengiriman data absen dan laporan langsung berkomunikasi ke server resmi Kemnaker (`monev-api.maganghub.kemnaker.go.id`).
   * Jika fitur AI diaktifkan, permintaan prompt hanya dikirim langsung ke Google Gemini API (`generativelanguage.googleapis.com`) menggunakan API Key pribadi Anda.
   * Notifikasi Telegram hanya dikirim ke bot resmi Telegram (`api.telegram.org`).
3. **Kata Sandi Tidak Disimpan**: Anda tidak diminta memasukkan password ke dalam file teks atau skrip. Login dilakukan langsung di jendela browser resmi MagangHub (melalui Playwright). Sesi login (token) disimpan di file `token.json` di komputer Anda sendiri.
4. **Kode Sumber Terbuka (Open Source)**: Seluruh baris kode Python dan Batch dapat Anda buka, periksa, dan audit kapan saja menggunakan Notepad atau Text Editor. Tidak ada kode terenkripsi atau *keylogger*.
5. **Perlindungan Data Rahasia**: Konfigurasi bawaan (`.gitignore`) telah disetel agar file token, catatan harian, dan kunci API tidak akan pernah ikut terunggah jika Anda mencadangkan folder ini ke Git/GitHub.

---

## 1. Apa yang Dilakukan Aplikasi Ini?

Aplikasi ini memudahkan peserta MagangHub Kemnaker dalam mengisi **Laporan Harian (Daily Log)** dan presensi.

Anda cukup menuliskan poin-poin kasar aktivitas kerja hari ini, contoh:
```text
08.00 maintenance server database, backup data keuangan, cek jaringan lab
```

Aplikasi (dengan bantuan Google Gemini AI) akan merapikannya menjadi 3 kolom laporan resmi:
* **Aktivitas Harian (`activity_log`)**: Ditulis rapi dan profesional sesuai jam kerja.
* **Pelajaran yang Didapat (`lesson_learned`)**: Ringkasan pembelajaran kompetensi teknis.
* **Kendala (`obstacles`)**: Kendala yang dihadapi dan solusinya.

Lalu, cukup dengan satu klik, laporan akan langsung terkirim dan tersimpan ke portal MagangHub Kemnaker.

---

## 2. Persiapan Sebelum Memulai

Sebelum menjalankan aplikasi, pastikan komputer Anda memiliki dua aplikasi berikut:

| Kebutuhan | Keterangan & Link Unduh |
|---|---|
| **Windows** | Windows 10 atau Windows 11 (64-bit). |
| **Google Chrome** | Peramban web standar ([Unduh Chrome](https://www.google.com/chrome/)). |
| **Miniconda** | Pengelola environment Python otomatis ([Unduh Miniconda Windows 64-bit](https://docs.conda.io/en/latest/miniconda.html)). |

> [!TIP]
> **Cara Pasang Miniconda:** Cukup jalankan installer Miniconda yang sudah diunduh, lalu klik **Next > I Agree > Next > Next > Install > Finish** (gunakan semua pengaturan default, tidak perlu mengubah opsi apa pun).

---

## 3. Instalasi — Cukup Dilakukan Satu Kali

Setelah Miniconda terpasang di komputer Anda:

1. Buka folder aplikasi ini (`absen-maganghub`).
2. Cari dan **klik dua kali** file [**`SETUP_INSTAL.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/SETUP_INSTAL.bat).
3. Jendela hitam (Command Prompt) akan terbuka dan otomatis:
   * Mendeteksi instalasi Conda Anda.
   * Membuat lingkungan khusus bernama `maganghub` (Python 3.11).
   * Memasang modul yang diperlukan (`requests`, `playwright`, `pytz`, dll).
   * Memasang komponen browser otomatis.
   * Menyiapkan file `.env` dan folder penyimpanan.
4. Tunggu beberapa menit (butuh koneksi internet).
5. Setelah muncul tulisan hijau **SETUP SELESAI**, tekan sembarang tombol untuk menutup jendela.

*Mulai sekarang, Anda tidak perlu menjalankan `SETUP_INSTAL.bat` lagi.*

---

## 4. Alur Pemakaian Sehari-hari

Hanya ada dua langkah sederhana untuk penggunaan sehari-hari:

```
[ LOGIN_MAGANGHUB.bat ]  ──> Login SSO di browser (jika sesi habis)
         │
         ▼
[  buka_aplikasi.bat  ]  ──> Tulis catatan ──> Generate AI ──> Kirim Laporan!
```

### Langkah A: Login (Hanya saat awal atau jika sesi habis)
1. Klik dua kali [**`LOGIN_MAGANGHUB.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/LOGIN_MAGANGHUB.bat).
2. Jendela browser Chrome akan terbuka otomatis menampilkan halaman MagangHub Kemnaker.
3. Masuk (*Sign In*) dengan akun Anda seperti biasa.
4. Setelah berhasil masuk dan halaman dashboard MagangHub terbuka, **tutup jendela browser**.
5. Sesi Anda kini tersimpan aman di file lokal `token.json` (biasanya bertahan beberapa hari/minggu tanpa perlu login ulang).

### Langkah B: Buka Aplikasi & Kirim Laporan
1. Klik dua kali [**`buka_aplikasi.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/buka_aplikasi.bat).
2. Aplikasi jendela desktop akan muncul:
   * **Tanggal & Status**: Sudah otomatis terisi tanggal hari ini dan status `PRESENT` (Hadir).
   * **Catatan aktivitas**: Ketikkan poin-poin singkat pekerjaan Anda hari ini.
   * Tekan tombol **Generate via Gemini (Ctrl+Enter)**.
   * Dalam beberapa detik, ketiga kotak di bawahnya (*Aktivitas Harian*, *Pelajaran*, *Kendala*) akan terisi rapi.
   * Anda bebas mengedit atau menambahkan isi kotak jika dirasa ada yang perlu disesuaikan.
   * Klik tombol hijau **Kirim Laporan Harian MagangHub**.
3. Notifikasi banner hijau akan muncul jika laporan berhasil terkirim dan tercatat di server Kemnaker.

---

## 5. Ringkasan File yang Dapat Digunakan

Pengguna biasa **hanya perlu menggunakan 3 file utama** berikut:

| Nama File | Kapan Digunakan |
|---|---|
| [**`SETUP_INSTAL.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/SETUP_INSTAL.bat) | Dijalankan **sekali saja** saat pertama kali memasang aplikasi di komputer. |
| [**`LOGIN_MAGANGHUB.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/LOGIN_MAGANGHUB.bat) | Dijalankan jika muncul pesan "Sesi habis" atau saat pertama kali setup login. |
| [**`buka_aplikasi.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/buka_aplikasi.bat) | Dijalankan **setiap hari kerja** untuk mengisi dan mengirim laporan harian. |

> [!NOTE]
> Jika ingin membuka aplikasi dari Desktop, klik kanan file `buka_aplikasi.bat` > **Send to > Desktop (create shortcut)**. Jangan memindahkan (*cut/move*) filenya langsung keluar dari folder ini.

---

## 6. Pengaturan Opsional (AI Gemini & Telegram)

Aplikasi tetap dapat dipakai manual tanpa Gemini maupun Telegram. Namun jika Anda ingin fitur otomatis AI aktif:

1. Buka file [**`.env`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/.env) menggunakan **Notepad**.
2. **Kunci AI Gemini (Gratis)**:
   * Dapatkan kunci API secara gratis di [Google AI Studio](https://aistudio.google.com/apikey).
   * Tempelkan kunci tersebut pada baris:
     ```env
     GEMINI_API_KEY=AIzaSy...
     ```
3. **Notifikasi Bot Telegram (Opsional)**:
   * Jika ingin mendapatkan pesan notifikasi pengingat absen di HP melalui Telegram, isi:
     ```env
     TELEGRAM_BOT_TOKEN=123456789:ABC...
     TELEGRAM_CHAT_ID=987654321
     ```
4. Simpan file (`Ctrl + S`) lalu tutup Notepad.

---

## 7. Pengisian Otomatis Terjadwal (Opsional)

Jika Anda tidak ingin repot membuka aplikasi setiap malam:

1. Buat catatan harian di dalam folder `notes/` dengan nama tanggal hari ini, contoh:
   * File: `notes/2026-10-29.txt`
   * Isi: Poin pekerjaan Anda hari ini.
2. Klik dua kali [**`daftar_task_scheduler.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/daftar_task_scheduler.bat).
3. Windows Task Scheduler akan otomatis:
   * Memeriksa hari libur nasional atau libur mingguan (jika libur, otomatis dilewati).
   * Setiap pukul **22.00 WIB**, skrip akan membaca catatan tersebut, meminta AI menyusunnya, dan mengirimkannya ke MagangHub secara otomatis di latar belakang.
   * Mengirimkan notifikasi keberhasilan ke Telegram Anda (jika bot dikonfigurasi).

Untuk menonaktifkan jadwal ini kembali, cukup klik dua kali [**`hapus_task_scheduler.bat`**](file:///c:/Utilities/bim_fixcode/absen-maganghub/hapus_task_scheduler.bat).

---

## 8. Panduan Mengatasi Masalah (FAQ)

| Kendala | Penyebab Umum | Solusi Praktis |
|---|---|---|
| **Miniconda tidak ditemukan saat instalasi** | Miniconda belum terpasang atau baru saja dipasang. | Pasang Miniconda dari tautan di atas, tutup jendela installer, lalu buka kembali `SETUP_INSTAL.bat`. |
| **Gagal mengirim (401 - Unauthorized)** | Sesi login Anda telah habis atau kedaluwarsa. | Klik dua kali `LOGIN_MAGANGHUB.bat`, login kembali di browser, lalu tutup browser setelah dashboard muncul. |
| **Gagal generate: GEMINI_API_KEY belum diisi** | Kunci AI belum dimasukkan di `.env`. | Buka `.env` dengan Notepad dan isi kunci API Anda, atau isi ketiga kotak laporan secara manual lalu klik tombol kirim. |
| **Laporan gagal: Status 409 (Conflict)** | Laporan untuk tanggal yang dipilih sudah pernah dikirim sebelumnya. | MagangHub hanya memperbolehkan satu entri per hari. Periksa tanggal di bagian atas aplikasi. |
| **Gagal 403 (Forbidden)** | Server Kemnaker memperbarui kode versi build frontend. | Perbarui nilai `FRONTEND_BUILD_ID` di file `.env` mengikuti instruksi di [README.md](file:///c:/Utilities/bim_fixcode/absen-maganghub/README.md). |
