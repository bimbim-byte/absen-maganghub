import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

import pytz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE_PATH)
except ImportError:
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

from maganghub_api import load_token_data
import gemini_helper

STATUS_CHOICES = ["PRESENT", "SICK", "LEAVE", "ABSENT"]


class LogApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._alive = True
        self._busy = False
        self.corpus_count = 0

        root.title("Asisten Laporan Harian MagangHub")
        root.geometry("780x742")
        root.minsize(660, 580)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self._load_corpus_async()

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
        ttk.Entry(top, textvariable=self.date_var, width=14).pack(side="left", padx=(6, 18))

        ttk.Label(top, text="Status").pack(side="left")
        self.status_var = tk.StringVar(value="PRESENT")
        ttk.Combobox(
            top, textvariable=self.status_var, values=STATUS_CHOICES,
            state="readonly", width=12,
        ).pack(side="left", padx=(6, 18))

        self.corpus_label = ttk.Label(top, text="korpus: memuat...", foreground="#666")
        self.corpus_label.pack(side="right")

        # --- Input catatan mentah -------------------------------------
        ttk.Label(
            self.root, text="Catatan aktivitas (input Anda)",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(10, 2))

        self.txt_notes = scrolledtext.ScrolledText(self.root, height=8, wrap="word")
        self.txt_notes.grid(row=2, column=0, sticky="nsew", **pad)
        self.txt_notes.bind("<Control-Return>", lambda e: self.on_generate())

        genbar = ttk.Frame(self.root)
        genbar.grid(row=3, column=0, sticky="ew", **pad)
        self.btn_generate = ttk.Button(
            genbar, text="Generate via Gemini  (Ctrl+Enter)", command=self.on_generate
        )
        self.btn_generate.pack(side="left")
        ttk.Button(genbar, text="Bersihkan", command=self.on_clear).pack(side="left", padx=8)

        # --- Hasil (editable) -----------------------------------------
        self.txt_activity = self._labeled_box(
            row=4, title="Aktivitas Harian", height=8,
            hint="(activity_log) hasil AI, boleh diedit",
        )
        self.txt_lesson = self._labeled_box(
            row=6, title="Pelajaran yang Didapat", height=5,
            hint="(lesson_learned)",
        )
        self.txt_obstacles = self._labeled_box(
            row=8, title="Kendala", height=4,
            hint="(obstacles)",
        )

        # --- Banner status pengiriman --------------------------------
        self.banner = ttk.Label(
            self.root, text="", anchor="center", padding=(8, 7),
            font=("Segoe UI", 10, "bold"),
        )
        self.banner.grid(row=10, column=0, sticky="ew", padx=10, pady=(10, 0))

        # --- Aksi bawah ----------------------------------------------
        bottom = ttk.Frame(self.root)
        bottom.grid(row=11, column=0, sticky="ew", padx=10, pady=(6, 4))
        ttk.Button(bottom, text="Simpan Draft", command=self.on_save_draft).pack(side="left")
        self.btn_send = ttk.Button(
            bottom, text="Kirim Laporan Harian MagangHub", command=self.on_send
        )
        self.btn_send.pack(side="left", padx=8)

        self.status_bar = ttk.Label(
            self.root, text="Siap.", anchor="w", relief="sunken", padding=(6, 3)
        )
        self.status_bar.grid(row=12, column=0, sticky="ew")

        # Bobot baris
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(5, weight=2)
        self.root.rowconfigure(7, weight=1)
        self.root.rowconfigure(9, weight=1)

    def _labeled_box(self, row: int, title: str, height: int, hint: str = ""):
        header = ttk.Frame(self.root)
        header.grid(row=row, column=0, sticky="w", padx=10, pady=(8, 0))
        ttk.Label(header, text=title, font=("Segoe UI", 10, "bold")).pack(side="left")
        if hint:
            ttk.Label(header, text=f"  {hint}", foreground="#666").pack(side="left")

        box = scrolledtext.ScrolledText(self.root, height=height, wrap="word")
        box.grid(row=row + 1, column=0, sticky="nsew", padx=10, pady=(2, 0))
        return box

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
        """Banner status besar: info (biru), success (hijau), error (merah)."""
        if not self._alive:
            return
        styles = {
            "info":    {"background": "#e8f1fb", "foreground": "#12558f"},
            "success": {"background": "#e6f6ea", "foreground": "#1a7f37"},
            "error":   {"background": "#fdeceb", "foreground": "#a5211a"},
        }
        style = styles.get(kind, styles["info"])
        try:
            self.banner.config(text=text, **style)
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
            prompt = gemini_helper.build_prompt(notes, examples)
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
        try:
            datetime.strptime(payload["date"], "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Tanggal salah", "Format tanggal harus YYYY-MM-DD.")
            return False
        if not payload["activity_log"]:
            messagebox.showwarning("Belum ada isi", "activity_log masih kosong.")
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