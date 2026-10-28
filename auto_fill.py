import os
import sys
import json
import argparse
import pytz
from datetime import datetime, timedelta

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

from main import (
    CONFIG,
    load_token_data,
    get_user_info,
    get_holiday_info,
    fetch_with_auto_refresh,
    send_telegram_message,
)
import generate_log

NOTES_DIR = os.path.join(BASE_DIR, "notes")
DRAFT_DIR = os.path.join(BASE_DIR, "drafts")

HARI_ID = {
    "MONDAY": "Senin", "TUESDAY": "Selasa", "WEDNESDAY": "Rabu",
    "THURSDAY": "Kamis", "FRIDAY": "Jumat", "SATURDAY": "Sabtu", "SUNDAY": "Minggu",
}


def load_notes(date_str: str) -> str:
    """Baca catatan aktivitas dari notes/YYYY-MM-DD.txt"""
    path = os.path.join(NOTES_DIR, f"{date_str}.txt")
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Gagal membaca {path}: {e}")
        return ""


def log_already_filled(participant_id: str, date_str: str):
    """
    Status log untuk tanggal tsb.
      True  -> sudah ada dan berisi
      False -> belum ada
      None  -> tidak bisa dipastikan (jaringan/sesi), jangan mengirim apa pun
    """
    url = f"{CONFIG['MONEV_API_BASE']}/daily-logs"
    params = {
        "date": date_str,
        "participant_id": participant_id,
        "limit": CONFIG["LIMIT"],
        "page": 0,
    }
    try:
        res = fetch_with_auto_refresh("GET", url, params=params)
    except Exception as e:
        print(f"Cek log error: {e}")
        return None

    if res.status_code != 200:
        print(f"Cek log gagal (HTTP {res.status_code}).")
        return None

    try:
        items = res.json().get("data", [])
    except Exception:
        return None

    for item in items:
        if not isinstance(item, dict):
            continue
        if (item.get("date") or "")[:10] != date_str:
            continue
        if (item.get("activity_log") or "").strip():
            return True
    return False


def save_draft(date_str: str, payload: dict) -> None:
    os.makedirs(DRAFT_DIR, exist_ok=True)
    path = os.path.join(DRAFT_DIR, f"{date_str}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Draft: {path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Isi daily log otomatis bila belum ada (dijadwalkan Task Scheduler)."
    )
    parser.add_argument(
        "--target", choices=["today", "yesterday"], default="today",
        help="Tanggal yang diisi (default: today)",
    )
    parser.add_argument(
        "--submit", action="store_true",
        help="Kirim ke server. Tanpa flag ini hanya menyiapkan draft.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Tetap proses walau log sudah terisi (hati-hati: bisa menimpa).",
    )
    parser.add_argument(
        "--ignore-hour", action="store_true",
        help="Abaikan batas jam (untuk uji coba manual).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    today = now.date()

    target = today if args.target == "today" else today - timedelta(days=1)
    date_str = target.isoformat()
    nama_hari = HARI_ID.get(target.strftime("%A").upper(), "")

    print(f"[auto_fill] target={date_str} submit={args.submit}")

    # --- Guard jam: jangan kirim sebelum jam yang ditentukan ----------
    try:
        fill_hour = int(os.getenv("FILL_HOUR", "8"))
    except ValueError:
        fill_hour = 8

    if args.submit and not args.ignore_hour and now.hour < fill_hour:
        print(f"Belum pukul {fill_hour:02d}:00 WIB (sekarang {now.strftime('%H:%M')}). Keluar.")
        return 0

    load_token_data()

    user = get_user_info()
    participant_id = user.get("participant_id")
    if not participant_id:
        print("Participant ID tidak ditemukan. Dibatalkan.")
        return 1

    # --- Hari libur: tidak perlu diisi -------------------------------
    day_en = target.strftime("%A").upper()
    if day_en in (user.get("off_days") or []):
        print(f"{date_str} hari libur mingguan. Dilewati.")
        return 0

    holiday = get_holiday_info(date_str)
    if holiday:
        print(f"{date_str} libur nasional: {holiday.get('name')}. Dilewati.")
        return 0

    # --- Sudah terisi? -----------------------------------------------
    status = log_already_filled(participant_id, date_str)
    if status is None:
        print("Status log tidak dapat dipastikan. Tidak ada yang dikirim.")
        return 3
    if status and not args.force:
        print(f"Daily log {date_str} sudah terisi. Dilewati.")
        return 0

    # --- Catatan aktivitas -------------------------------------------
    notes = load_notes(date_str)
    if not notes:
        msg = (
            f"*Catatan belum tersedia*\n\n"
            f"Daily log {nama_hari}, {date_str} belum diisi, "
            f"tetapi belum ada catatan aktivitas.\n\n"
            f"Buat file: `notes/{date_str}.txt`"
        )
        if args.submit:
            send_telegram_message(msg, is_silent=False)
        print(f"Catatan notes/{date_str}.txt tidak ada. Dibatalkan.")
        return 2

    # --- Generate via Gemini -----------------------------------------
    examples = generate_log.load_corpus()
    print(f"Few-shot: {len(examples)} contoh.")

    try:
        generated = generate_log.call_gemini(
            generate_log.build_prompt(notes, examples)
        )
    except Exception as e:
        print(f"Gagal generate: {e}")
        if args.submit:
            send_telegram_message(
                f"*Gagal generate log* ({date_str})\n\n`{str(e)[:300]}`",
                is_silent=False,
            )
        return 1

    payload = generate_log.build_payload(date_str, generated)
    save_draft(date_str, payload)
    generate_log.print_preview(payload)

    if not args.submit:
        print("Mode draft: tidak ada yang dikirim.")
        return 0

    # --- Kirim -------------------------------------------------------
    ok, message = generate_log.submit_payload(payload)
    print(message)

    if ok:
        send_telegram_message(
            f"*Daily log terisi otomatis*\n\n"
            f"Tanggal: {nama_hari}, {date_str}\n"
            f"Status: PRESENT",
            is_silent=True,
        )
        return 0

    send_telegram_message(
        f"*Gagal mengisi daily log* ({date_str})\n\n"
        f"{message}\n\n"
        f"Draft tersimpan di `drafts/{date_str}.json`.",
        is_silent=False,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
