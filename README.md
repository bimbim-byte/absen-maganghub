# Absen & Laporan MagangHub Kemnaker

Aplikasi bantu untuk **peserta magang MagangHub Kemnaker**: mengubah catatan aktivitas harian Anda menjadi laporan kerja formal secara otomatis dengan bantuan AI, lalu mengirimkannya ke sistem MagangHub.

---

## Daftar Isi

- [Apa yang Dilakukan Aplikasi Ini](#apa-yang-dilakukan-aplikasi-ini)
- [Apakah Aman?](#apakah-aman)
- [Persiapan Sebelum Memulai](#persiapan-sebelum-memulai)
- [Instalasi — Sekali Saja](#instalasi--sekali-saja)
- [Pemakaian Sehari-hari](#pemakaian-sehari-hari)
- [Tombol Cepat Kategori](#tombol-cepat-kategori)
- [Pengisian Otomatis Terjadwal](#pengisian-otomatis-terjadwal-opsional)
- [Pengaturan Opsional](#pengaturan-opsional)
- [Daftar Berkas Penting](#daftar-berkas-penting)
- [Jika Ada Masalah](#jika-ada-masalah)
- [Catatan & Tanggung Jawab](#catatan--tanggung-jawab)

---

## Apa yang Dilakukan Aplikasi Ini

1. Anda menulis catatan singkat aktivitas hari ini.
2. AI (Google Gemini) mengubahnya menjadi tiga bagian laporan yang rapi:
   - **Aktivitas Harian** — apa yang Anda kerjakan
   - **Pelajaran yang Didapat** — ilmu yang Anda peroleh
   - **Kendala** — hambatan yang dihadapi
3. Laporan dikirim langsung ke akun MagangHub Anda.

Aplikasi ini juga bisa:
- **Mengingatkan** Anda lewat Telegram jika laporan hari ini belum diisi.
- **Mengisi otomatis** setiap hari pada jam tertentu (opsional).
- **Belajar dari laporan lama** Anda, agar gaya bahasa hasil AI mirip dengan kebiasaan Anda.

---

## Apakah Aman?

Ya. Aplikasi ini dibuat dengan prinsip **lokal dan tanpa perantara**:

- **Tidak ada server pihak ketiga.** Semua proses berjalan di komputer Anda sendiri. Pengembang tidak mengumpulkan data apa pun.
- **Data dikirim langsung ke tujuan resmi.** Laporan ke `monev-api.maganghub.kemnaker.go.id`, teks laporan ke Google Gemini, notifikasi ke Telegram. Tidak lewat mana pun selain itu.
- **Kata sandi Anda tidak pernah dibaca atau disimpan.** Login dilakukan di browser Chrome resmi. Yang tersimpan hanya tiket sesi (di berkas `token.json`), bukan sandi.
- **Kode terbuka.** Semua berkas bisa Anda periksa sendiri dengan editor teks biasa.
- **Berkas pribadi tidak ikut terunggah.** Berkas berisi data pribadi sudah dikecualikan agar tidak pernah terkirim ke repositori publik.

---

## Persiapan Sebelum Memulai

Siapkan dua hal berikut:

| Yang Dibutuhkan | Keterangan |
|---|---|
| **Miniconda** | Program pengelola Python. Unduh di situs resmi Miniconda. Pasang dengan pengaturan bawaan. |
| **Google Chrome** | Sudah terpasang di kebanyakan komputer. |
| **Akun MagangHub** | Akun peserta magang Anda yang biasa dipakai untuk absen. |
| **Koneksi internet** | Dibutuhkan saat instalasi dan saat mengirim laporan. |

> Nama berkas atau folder boleh berbeda di komputer Anda. Yang penting seluruh berkas aplikasi berada dalam **satu folder yang sama**.

---

## Instalasi — Sekali Saja

1. Letakkan seluruh berkas aplikasi dalam satu folder.
2. Klik dua kali berkas **`SETUP_INSTAL.bat`**.
3. Ikuti petunjuk di layar. Proses ini akan:
   - mencari Miniconda di komputer Anda,
   - membuat lingkungan kerja bernama `maganghub`,
   - memasang bahan-bahan yang dibutuhkan,
   - memasang browser untuk login,
   - menyiapkan berkas pengaturan dan folder kerja.
4. Tunggu hingga muncul tulisan **SETUP SELESAI**. Proses ini butuh **5 sampai 15 menit** bergantung kecepatan internet.

> **Jangan tutup jendela** selama proses berjalan. Instalasi hanya perlu dilakukan sekali.

Jika Muncul Pesan Miniconda Tidak Ditemukan:

1. Unduh dan pasang Miniconda dari situs resminya.
2. Tutup jendela yang sedang berjalan.
3. Jalankan `SETUP_INSTAL.bat` sekali lagi.

---

## Pemakaian Sehari-hari

### Langkah 1 — Login (hanya saat awal atau jika sesi habis)

1. Klik dua kali **`LOGIN_MAGANGHUB.bat`**.
2. Browser Chrome akan terbuka. Lakukan login seperti biasa.
3. Setelah halaman dashboard MagangHub terbuka, **tutup jendela browser**.
4. Sesi Anda tersimpan otomatis dan biasanya bertahan beberapa hari.

### Langkah 2 — Isi dan Kirim Laporan

1. Klik dua kali **`buka_aplikasi.bat`**.
2. Jendela aplikasi terbuka. Isinya terbagi dua kolom:
   - **Kolom kiri** — tempat Anda menulis catatan dan menekan tombol Generate.
   - **Kolom kanan** — tempat hasil laporan muncul dan tombol Kirim berada.

**Alur singkat:**

```
 Klik tombol kategori  →  Lengkapi catatan  →  Generate  →  Kirim
     (kolom kiri)           (kolom kiri)      (kolom kiri)  (kolom kanan)
```

3. **Tanggal dan Status** sudah terisi otomatis. Ubah bila perlu.
4. Tulis catatan singkat di kolom kiri, atau klik tombol kategori untuk memakai template siap pakai.
5. Tekan **Generate via Gemini** (atau tekan `Ctrl+Enter`).
6. Hasil laporan muncul di kolom kanan. Anda bebas mengeditnya.
7. Tekan **Kirim ke MagangHub**. Pesan status akan muncul di baris bawah.

> **Tips:** Semakin jelas catatan Anda, semakin bagus hasil laporannya. Sebutkan jam, jenis pekerjaan, dan alat atau sistem yang Anda pakai.

---

## Tombol Cepat Kategori

Di kolom kiri tersedia tombol yang langsung mengisi catatan dengan template. Cocok saat Anda tidak ingin menulis dari nol.

| Tombol | Untuk Hari Seperti Apa |
|---|---|
| **Masuk Pagi** | Hari kerja biasa yang dimulai pagi. |
| **Masuk Siang** | Hari kerja dengan jadwal shift siang. |
| **Libur** | Hari libur pengganti pada hari kerja. Absen tetap wajib diisi meski tidak ada aktivitas teknis. |
| **Piket Akhir Pekan** | Saat Anda masuk kerja pada Sabtu atau Minggu. |
| **Belajar Mandiri** | Hari tanpa pekerjaan lapangan, dipakai untuk belajar. |

Setelah memilih template, lengkapi detailnya lalu tekan Generate. Tombol **Bersihkan** menghapus seluruh isian.

---

## Pengisian Otomatis Terjadwal (Opsional)

Bila Anda ingin laporan terisi sendiri tanpa membuka aplikasi, jalankan **`daftar_task_scheduler.bat`**. Tiga jadwal akan dibuat:

| Jadwal | Waktu | Kegunaan |
|---|---|---|
| Isi laporan | Setiap hari, malam | Mengisi laporan dari catatan harian yang Anda simpan di folder `notes`. |
| Cek kehadiran | Setiap 30 menit | Mengirim pengingat lewat Telegram jika laporan belum diisi. |
| Ambil riwayat | Setiap Minggu malam | Menyegarkan data laporan lama agar gaya AI tetap sesuai. |

**Cara kerja pengisian otomatis:** simpan catatan Anda sebagai berkas teks di dalam folder `notes`, dengan nama sesuai tanggal. Bila berkas itu belum ada, aplikasi akan membuatkannya otomatis berisi contoh, lalu Anda cukup melengkapinya.

Untuk menghentikan jadwal, jalankan **`hapus_task_scheduler.bat`**.

---

## Pengaturan Opsional

Buka berkas **`.env`** dengan Notepad untuk mengubah pengaturan. Semua bersifat opsional.

| Pengaturan | Fungsi | Perlu Diisi? |
|---|---|---|
| `GEMINI_API_KEY` | Kunci AI agar laporan ditulis otomatis. | **Sangat disarankan.** Dapat gratis di situs Google AI Studio. |
| `TELEGRAM_BOT_TOKEN` | Token bot untuk pengingat Telegram. | Opsional. |
| `TELEGRAM_CHAT_ID` | ID obrolan tujuan notifikasi. | Opsional. |
| `MULAI_BULAN` / `AKHIR_BULAN` | Rentang bulan untuk menarik riwayat laporan lama. | Isi sesuai masa magang. |
| `START_HOUR` / `END_HOUR` | Jam pengiriman notifikasi. | Jarang diubah. |

Setelah mengubah `.env`, simpan berkasnya lalu buka ulang aplikasi.

---

## Daftar Berkas Penting

**Berkas yang Anda klik untuk memakai aplikasi:**

| Berkas | Kapan Dijalankan |
|---|---|
| `SETUP_INSTAL.bat` | **Sekali saja** saat pertama memasang. |
| `LOGIN_MAGANGHUB.bat` | Saat pertama kali, atau ketika muncul pesan sesi habis. |
| `buka_aplikasi.bat` | **Setiap hari** untuk mengisi dan mengirim laporan. |
| `daftar_task_scheduler.bat` | Opsional. Menyalakan pengisian otomatis. |
| `hapus_task_scheduler.bat` | Opsional. Mematikan pengisian otomatis. |

> Ingin pintasan di Desktop? Klik kanan `buka_aplikasi.bat` lalu pilih **Send to → Desktop (create shortcut)**. Jangan pindahkan berkasnya keluar dari folder aplikasi.

**Berkas yang tidak perlu Anda buka:**

Berkas berakhiran `.py` adalah program inti, dan berkas berakhiran `.md` adalah dokumentasi. Keduanya tidak perlu dibuka untuk memakai aplikasi.

---

## Jika Ada Masalah

| Gejala | Penyebab Umum | Solusi |
|---|---|---|
| Jendela langsung tertutup saat berkas `.bat` diklik | Python atau lingkungan kerja belum siap | Jalankan `SETUP_INSTAL.bat`, lalu coba lagi. |
| Muncul pesan "Sesi habis" atau gagal kirim | Sesi login kedaluwarsa | Jalankan `LOGIN_MAGANGHUB.bat`, login ulang. |
| Muncul pesan build ID usang | Pengaturan aplikasi perlu diperbarui | Hubungi pembuat aplikasi untuk memperbarui pengaturan. |
| Laporan tidak terkirim karena tanggal | Tanggal sudah terisi atau format salah | Periksa tanggal pada aplikasi, format harus `Tahun-Bulan-Hari`. |
| Tombol Generate tidak berevolusi | Kunci AI belum diisi | Isi `GEMINI_API_KEY` pada berkas `.env`. |
| Jadwal otomatis tidak berjalan | Komputer mati atau task belum terdaftar | Nyalakan ulang komputer, jalankan `daftar_task_scheduler.bat` sebagai Administrator. |

> Untuk pengecekan mendalam, buka folder aplikasi dan lihat berkas berakhiran `.log`. Berkas itu mencatat pesan saat jadwal otomatis berjalan.

---

## Catatan & Tanggung Jawab

- Aplikasi ini adalah alat bantu pribadi, **bukan bagian resmi** dari MagangHub Kemnaker.
- Anda tetap bertanggung jawab memastikan laporan sesuai dengan aktivitas yang benar-benar Anda kerjakan.
- Gunakan wajar. Jangan mengirim laporan fiktif.
- Berkas berisi data pribadi Anda dikecualikan dari repositori publik, tetapi **jangan bagikan berkas `token.json` atau `.env`** kepada siapa pun karena berisi kunci akses akun Anda.
