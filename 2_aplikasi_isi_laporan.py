import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import pytz
from env_loader import load_env
load_env()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from maganghub_api import load_token_data
import gemini_helper
import log_classifier

STATUS_CHOICES = ["PRESENT", "SICK", "LEAVE", "ABSENT"]

# Template catatan siap-pakai per kategori tipe hari.
# Teks mengikuti gaya penulisan pada activity_logs.json historis.
TEMPLATE_CATATAN = {
    "Masuk Pagi": (
        "08.00 - 10.00: \n"
        "10.30: \n"
        "13.30: \n"
        "15.00 - 16.00: \n\n"
        "Catatan: sesuaikan penanda waktu (HH.MM) dengan jam kerja sebenarnya."
    ),
    "Masuk Siang": (
        "13.00 - 15.00: \n"
        "15.30: \n"
        "16.30 - Selesai: \n\n"
        "Catatan: sesuaikan penanda waktu (HH.MM) dengan jadwal shift siang Anda."
    ),
    "Libur": (
        "08.00 - 17.00: Hari libur/off operasional "
        "(pengganti jadwal piket/masuk kerja pada hari Sabtu).\n\n"
        "Catatan: ini hari libur pengganti pada hari kerja (Senin-Jumat). "
        "Absen tetap wajib diisi meskipun tidak ada aktivitas teknis."
    ),
    "Piket Akhir Pekan": (
        "08.00 - 17.00: Melaksanakan jadwal piket operasional pada hari "
        "libur akhir pekan (Sabtu/Minggu).\n\n"
        "Catatan: masuk kerja di luar hari kerja biasa. Cek jadwal piket Anda."
    ),
    "Belajar Mandiri": (
        "Aktivitas pembelajaran berfokus pada studi konsep ...\n"
        "Pembelajaran meliputi ...\n\n"
        "Catatan: hari tanpa aktivitas operasional, dipakai untuk belajar."
    ),
}


class LogApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._alive = True
        self._busy = False
        self.corpus_count = 0
        self.insight = {}        # ringkasan dari log_classifier
        self.ringkasan = {}      # ringkasan penuh untuk saran

        root.title("Asisten Laporan Harian MagangHub")

        # Ukuran adaptif dari resolusi layar pengguna
        lebar, tinggi = self._hitung_ukuran(root)
        root.geometry(self._posisi_tengah(root, lebar, tinggi))
        root.minsize(780, 500)

        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self._load_corpus_async()
        self._load_insight_async()

    # ------------------------------------------------------------------
    # Ukuran adaptif
    # ------------------------------------------------------------------
    @staticmethod
    def _hitung_ukuran(root: tk.Tk) -> tuple:
        """
        Hitung ukuran window dari resolusi layar, sisakan ruang taskbar.
        Layout kiri-kanan butuh lebar memadai: target 72% lebar layar,
        dibatasi 760-1180px. Tinggi 84% agar tombol bawah tidak tertutup taskbar.
        """
        root.update_idletasks()
        try:
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
        except tk.TclError:
            return 1080, 700

        lebar = min(1180, max(760, int(sw * 0.72)))
        tinggi = min(900, max(540, int(sh * 0.84)))
        return lebar, tinggi

    @staticmethod
    def _posisi_tengah(root: tk.Tk, lebar: int, tinggi: int) -> str:
        """Tempatkan window di tengah layar, agak ke atas."""
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = max(0, (sw - lebar) // 2)
        y = max(0, int((sh - tinggi) * 0.35))
        return f"{lebar}x{tinggi}+{x}+{y}"

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 4}
        self.root.columnconfigure(0, weight=1)

        # --- Baris atas: tanggal & status -----------------------------
        top = ttk.Frame(self.root)
        top.grid(row=0, column=0, sticky="ew", **pad)

        ttk.Label(top, text="Tanggal").pack(side="left")
        self.date_var = tk.StringVar(
            value=datetime.now(pytz.timezone("Asia/Jakarta")).date().isoformat()
        )
        ttk.Entry(top, textvariable=self.date_var, width=12).pack(side="left", padx=(6, 14))

        ttk.Label(top, text="Status").pack(side="left")
        self.status_var = tk.StringVar(value="PRESENT")
        ttk.Combobox(
            top, textvariable=self.status_var, values=STATUS_CHOICES,
            state="readonly", width=10,
        ).pack(side="left", padx=(6, 14))

        self.corpus_label = ttk.Label(top, text="memuat...", foreground="#666")
        self.corpus_label.pack(side="right")

        # --- Area kerja: kiri (input) | kanan (hasil) ------------------
        kerja = ttk.Frame(self.root)
        kerja.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 0))
        kerja.columnconfigure(0, weight=5, minsize=340)
        kerja.columnconfigure(1, weight=6, minsize=340)
        kerja.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        kiri = ttk.LabelFrame(kerja, text=" 1. Catatan Aktivitas ", padding=(6, 4))
        kiri.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        kiri.columnconfigure(0, weight=1)
        kiri.rowconfigure(2, weight=1)

        kanan = ttk.LabelFrame(kerja, text=" 2. Hasil Laporan ", padding=(6, 4))
        kanan.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        kanan.columnconfigure(0, weight=1)
        kanan.rowconfigure(1, weight=3)
        kanan.rowconfigure(3, weight=2)
        kanan.rowconfigure(5, weight=1)

        self._build_panel_kiri(kiri)
        self._build_panel_kanan(kanan)

        # --- Zona aksi: Generate (kiri) & Kirim (kanan) ---------------
        aksi = ttk.Frame(self.root)
        aksi.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 4))
        aksi.columnconfigure(0, weight=5, minsize=340)
        aksi.columnconfigure(1, weight=6, minsize=340)

        zona_kiri = ttk.Frame(aksi)
        zona_kiri.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.btn_generate = ttk.Button(
            zona_kiri, text="Generate via Gemini (Ctrl+Enter)", command=self.on_generate
        )
        self.btn_generate.pack(fill="x")

        sub_kiri = ttk.Frame(zona_kiri)
        sub_kiri.pack(fill="x", pady=(4, 0))
        ttk.Button(sub_kiri, text="Muat Catatan", command=self.on_load_notes).pack(
            side="left", expand=True, fill="x")
        ttk.Button(sub_kiri, text="Bersihkan", command=self.on_clear).pack(
            side="left", expand=True, fill="x", padx=(4, 0))

        zona_kanan = ttk.Frame(aksi)
        zona_kanan.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.btn_send = ttk.Button(
            zona_kanan, text="Kirim ke MagangHub", command=self.on_send
        )
        self.btn_send.pack(fill="x")

        sub_kanan = ttk.Frame(zona_kanan)
        sub_kanan.pack(fill="x", pady=(4, 0))
        ttk.Button(sub_kanan, text="Simpan Draft", command=self.on_save_draft).pack(
            side="left", expand=True, fill="x")
        ttk.Button(sub_kanan, text="Perbarui Saran", command=self._load_insight_async).pack(
            side="left", expand=True, fill="x", padx=(4, 0))

        # Banner status kirim (baris sendiri, ringkas)
        self.banner = ttk.Label(self.root, text="", anchor="w", padding=(4, 2))
        self.banner.grid(row=3, column=0, sticky="ew", padx=10)

        self.status_bar = ttk.Label(
            self.root, text="Siap.", anchor="w", relief="sunken", padding=(6, 2)
        )
        self.status_bar.grid(row=4, column=0, sticky="ew")

        # Saran mengikuti perubahan tanggal
        self.date_var.trace_add("write", lambda *_: self._refresh_saran())

    # ------------------------------------------------------------------
    # Panel kiri: input catatan
    # ------------------------------------------------------------------
    def _build_panel_kiri(self, parent):
        # Tombol kategori cepat
        kat = ttk.Frame(parent)
        kat.grid(row=0, column=0, sticky="ew")
        for i, nama in enumerate(TEMPLATE_CATATAN):
            ttk.Button(
                kat, text=nama,
                command=lambda n=nama: self.on_isi_kategori(n),
            ).grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 3), pady=(0, 3))
        for c in range(3):
            kat.columnconfigure(c, weight=1)

        hdr = ttk.Frame(parent)
        hdr.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Label(hdr, text="Tulis/kategori di atas:", foreground="#666",
                  font=("Segoe UI", 8)).pack(side="left")

        self.txt_notes = scrolledtext.ScrolledText(parent, height=6, width=1, wrap="word")
        self.txt_notes.grid(row=2, column=0, sticky="nsew", pady=(2, 4))
        self.txt_notes.bind("<Control-Return>", lambda e: self.on_generate())
        self.txt_notes.bind("<KeyRelease>", lambda e: self._refresh_saran())

        self.saran_text = tk.Text(
            parent, height=4, wrap="word", relief="flat", width=1,
            background="#f7f9fb", foreground="#444", font=("Segoe UI", 8),
        )
        self.saran_text.grid(row=3, column=0, sticky="ew", pady=(0, 2))
        self.saran_text.configure(state="disabled")

        self.insight_label = ttk.Label(parent, text="riwayat: memuat...",
                                       foreground="#666", font=("Segoe UI", 8))
        self.insight_label.grid(row=4, column=0, sticky="w")

    # ------------------------------------------------------------------
    # Panel kanan: hasil laporan
    # ------------------------------------------------------------------
    def _build_panel_kanan(self, parent):
        ttk.Label(parent, text="Aktivitas Harian (activity_log)",
                  font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w")
        self.txt_activity = scrolledtext.ScrolledText(parent, height=7, width=1, wrap="word")
        self.txt_activity.grid(row=1, column=0, sticky="nsew", pady=(2, 0))

        ttk.Label(parent, text="Pelajaran yang Didapat (lesson_learned)",
                  font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="w", pady=(6, 0))
        self.txt_lesson = scrolledtext.ScrolledText(parent, height=5, width=1, wrap="word")
        self.txt_lesson.grid(row=3, column=0, sticky="nsew", pady=(2, 0))

        ttk.Label(parent, text="Kendala (obstacles)",
                  font=("Segoe UI", 9, "bold")).grid(
            row=4, column=0, sticky="w", pady=(6, 0))
        self.txt_obstacles = scrolledtext.ScrolledText(parent, height=4, width=1, wrap="word")
        self.txt_obstacles.grid(row=5, column=0, sticky="nsew", pady=(2, 0))

    # ------------------------------------------------------------------
    # Helper thread-safe
    # ------------------------------------------------------------------
    def _run_async(self, fn, on_done):
        """Jalankan fn di thread lain agar UI tidak beku."""
        def worker():
            try:
                result = fn()
            except Exception as e:  # noqa: BLE001
                result = e
            if not self._alive:
                return
            try:
                self.root.after(0, lambda r=result: on_done(r))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def set_status(self, text: str, color: str = "#000"):
        if not self._alive:
            return
        self.status_bar.config(text=text, foreground=color)

    def set_banner(self, text: str, kind: str = "info"):
        """Teks status ringkas di baris aksi: info (biru), success (hijau), error (merah)."""
        if not self._alive:
            return
        warna = {
            "info": "#12558f",
            "success": "#1a7f37",
            "error": "#a5211a",
        }
        try:
            self.banner.config(text=text, foreground=warna.get(kind, warna["info"]))
        except tk.TclError:
            pass

    def set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        try:
            self.btn_generate.config(state=state)
            self.btn_send.config(state=state)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # Korpus few-shot
    # ------------------------------------------------------------------
    def _load_corpus_async(self):
        def work():
            return gemini_helper.load_corpus()

        def done(result):
            if isinstance(result, Exception):
                self.corpus_label.config(text="korpus: gagal dibaca")
                return
            self.corpus_count = len(result)
            if self.corpus_count:
                self.corpus_label.config(text=f"korpus: {self.corpus_count} contoh")
            else:
                self.corpus_label.config(
                    text="korpus: kosong (jalankan 1_ambil_data_log.py)",
                    foreground="#b58900",
                )

        self._run_async(work, done)

    # ------------------------------------------------------------------
    # Saran dari riwayat (log_classifier)
    # ------------------------------------------------------------------
    def _load_insight_async(self):
        def work():
            data = log_classifier.muat_activity(log_classifier.DEFAULT_INPUT)
            hasil = [log_classifier.klasifikasi_satu(i) for i in (data.get("activities") or [])]
            rk = log_classifier.rangkum(hasil, data)
            rk["insight"] = log_classifier.buat_insight(rk)
            return rk

        def done(result):
            if isinstance(result, Exception):
                self.insight_label.config(text="riwayat: tidak tersedia", foreground="#b58900")
                self._set_saran(["Riwayat belum tersedia. Jalankan 1_ambil_data_log.py."])
                return
            self.ringkasan = result
            self.insight = result.get("insight") or {}
            self.corpus_count = result.get("total_entri") or self.corpus_count
            n = result.get("total_entri", 0)
            self.insight_label.config(
                text=f"riwayat: {n} entri dipelajari", foreground="#666"
            )
            self._refresh_saran()

        self._run_async(work, done)

    def _set_saran(self, baris: list):
        try:
            self.saran_text.configure(state="normal")
            self.saran_text.delete("1.0", "end")
            self.saran_text.insert("1.0", "\n".join(f"• {b}" for b in baris))
            self.saran_text.configure(state="disabled")
        except tk.TclError:
            pass

    def _refresh_saran(self):
        """Hitung ulang saran berdasarkan tanggal & jam mulai pada catatan."""
        if not self.ringkasan:
            return
        date_str = self.date_var.get().strip()
        notes = self.txt_notes.get("1.0", "end").strip()
        waktu = log_classifier.ekstrak_waktu(notes)
        try:
            saran = log_classifier.saran_cepat(date_str, self.ringkasan,
                                               waktu.get("mulai_str"))
        except Exception:
            return
        self._set_saran([s["pesan"] for s in saran] or ["Belum ada saran khusus."])

    def on_load_notes(self):
        """Muat notes/YYYY-MM-DD.txt sesuai tanggal ke kotak catatan."""
        date_str = self.date_var.get().strip()
        path = os.path.join("notes", f"{date_str}.txt")
        if not os.path.exists(path):
            messagebox.showinfo("Tidak ada catatan", f"{path} belum ada.")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                isi = f.read().strip()
        except Exception as e:
            messagebox.showerror("Gagal baca", str(e))
            return
        self.txt_notes.delete("1.0", "end")
        self.txt_notes.insert("1.0", isi)
        self._refresh_saran()
        self.set_status(f"Catatan dimuat dari {path}", "#0b6")

    def on_isi_kategori(self, nama: str):
        """
        Isi kotak catatan dengan template kategori siap-pakai.
        Kategori 'Libur' sekaligus mengarahkan fokus ke tombol Generate.
        """
        template = TEMPLATE_CATATAN.get(nama)
        if not template:
            return

        # Jangan timpa catatan yang sudah ada tanpa konfirmasi
        isi_lama = self.txt_notes.get("1.0", "end").strip()
        if isi_lama and not messagebox.askyesno(
            "Ganti catatan?",
            f"Kotak catatan sudah ada isinya.\n\nGanti dengan template '{nama}'?",
        ):
            return

        self.txt_notes.delete("1.0", "end")
        self.txt_notes.insert("1.0", template)
        self.txt_notes.focus_set()
        self._refresh_saran()
        self.set_status(
            f"Template '{nama}' dimuat. Lengkapi detail, lalu tekan Generate (Ctrl+Enter).",
            "#12558f",
        )

    # ------------------------------------------------------------------
    # Aksi
    # ------------------------------------------------------------------
    def on_generate(self):
        if self._busy:
            return

        notes = self.txt_notes.get("1.0", "end").strip()
        if not notes:
            messagebox.showwarning("Catatan kosong", "Isi catatan aktivitas terlebih dahulu.")
            return

        self.set_busy(True)
        self.set_status("Menghubungi Gemini...", "#0b6")

        def work():
            examples = gemini_helper.load_corpus()
            prompt = gemini_helper.build_prompt(notes, examples, self.insight or None)
            return gemini_helper.call_gemini(prompt)

        def done(result):
            self.set_busy(False)
            if isinstance(result, Exception):
                self.set_status(f"Gagal: {result}", "#b00")
                messagebox.showerror("Gagal generate", str(result))
                return
            self._fill_outputs(result)
            self.set_status("Selesai. Periksa dan edit bila perlu.", "#0b6")

        self._run_async(work, done)

    def _fill_outputs(self, data: dict):
        for box, key in (
            (self.txt_activity, "activity_log"),
            (self.txt_lesson, "lesson_learned"),
            (self.txt_obstacles, "obstacles"),
        ):
            box.delete("1.0", "end")
            box.insert("1.0", data.get(key, ""))

    def on_clear(self):
        for box in (self.txt_notes, self.txt_activity, self.txt_lesson, self.txt_obstacles):
            box.delete("1.0", "end")
        self.set_status("Dibersihkan.")

    def collect_payload(self):
        return {
            "date": self.date_var.get().strip(),
            "status": self.status_var.get().strip() or "PRESENT",
            "activity_log": self.txt_activity.get("1.0", "end").strip(),
            "lesson_learned": self.txt_lesson.get("1.0", "end").strip(),
            "obstacles": self.txt_obstacles.get("1.0", "end").strip(),
        }

    def _validate(self, payload: dict) -> bool:
        if not payload["date"]:
            messagebox.showwarning("Tanggal kosong", "Isi tanggal terlebih dahulu.")
            return False
        try:
            datetime.strptime(payload["date"], "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Tanggal salah", "Format tanggal harus YYYY-MM-DD.")
            return False
        if not payload["activity_log"]:
            messagebox.showwarning(
                "Belum ada isi",
                "Aktivitas Harian masih kosong.\n\n"
                "Petunjuk: pakai tombol kategori (mis. 'Libur') untuk mengisi "
                "template catatan, lalu tekan Generate.",
            )
            return False
        return True

    def on_save_draft(self):
        payload = self.collect_payload()
        if not self._validate(payload):
            return
        path = os.path.join(gemini_helper.OUTPUT_FILE)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Gagal simpan", str(e))
            return
        self.set_status(f"Draft disimpan: {path}", "#0b6")

    def on_send(self):
        if self._busy:
            return

        payload = self.collect_payload()
        if not self._validate(payload):
            return

        if not messagebox.askyesno(
            "Konfirmasi kirim",
            f"Kirim daily log tanggal {payload['date']} ke server?\n\n"
            "Data akan tersimpan permanen di akun Anda.",
        ):
            return

        self.set_busy(True)
        self.set_status("Mengirim laporan...", "#0b6")
        self.set_banner("Mengirim... mohon tunggu", "info")

        def work():
            load_token_data()
            return gemini_helper.submit_payload(payload)

        def done(result):
            self.set_busy(False)

            if isinstance(result, Exception):
                text = f"Gagal mengirim: {result}"
                self.set_banner(text, "error")
                self.set_status(text, "#b00")
                return

            ok, message = result
            if ok:
                self.set_banner(
                    f"Berhasil! Laporan {payload['date']} sudah terkirim.", "success"
                )
                self.set_status(message, "#0b6")
            else:
                self.set_banner("Gagal mengirim. Laporan belum tersimpan.", "error")
                self.set_status(message, "#b00")
                # Detail lengkap ditampilkan supaya penyebabnya jelas
                messagebox.showerror("Pengiriman gagal", message)

        self._run_async(work, done)

    def on_close(self):
        self._alive = False
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    LogApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()