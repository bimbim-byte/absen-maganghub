import os
import sys
import json
import argparse
import pytz
from datetime import datetime, date

import requests

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

from maganghub_api import CONFIG, load_token_data, fetch_with_auto_refresh

CORPUS_FILE = os.path.join(BASE_DIR, "activity_logs.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "generated_log.json")

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "activity_log": {"type": "STRING"},
        "lesson_learned": {"type": "STRING"},
        "obstacles": {"type": "STRING"},
    },
    "required": ["activity_log", "lesson_learned", "obstacles"],
    "propertyOrdering": ["activity_log", "lesson_learned", "obstacles"],
}

SYSTEM_INSTRUCTION = (
    "Anda membantu seorang peserta magang bidang IT menulis daily log. "
    "Tulis dalam Bahasa Indonesia formal-teknis, memakai penanda waktu 24 jam "
    "(contoh: '07.50 - 08.30: ...'), dan pisahkan tiap pokok bahasan dengan "
    "baris kosong ganda. Ikuti gaya, kedalaman, dan panjang entri contoh. "
    "Jangan mengarang hasil yang tidak disebutkan pengguna."
)


def load_corpus(max_examples=6, max_chars=1200):
    """Ambil beberapa entri historis sebagai contoh gaya (few-shot)."""
    if not os.path.exists(CORPUS_FILE):
        print(f"[!] Korpus {CORPUS_FILE} tidak ditemukan, jalan tanpa few-shot.")
        return []

    try:
        with open(CORPUS_FILE, "r", encoding="utf-8") as f:
            corpus = json.load(f)
    except Exception as e:
        print(f"[!] Gagal membaca korpus: {e}")
        return []

    activities = corpus.get("activities", [])
    if not activities:
        print("[!] Korpus kosong. Jalankan 1_ambil_data_log.py dulu.")
        return []

    # Ambil dari belakang: entri terbaru gaya tulisannya paling relevan
    sample = activities[-max_examples:]

    examples = []
    for item in sample:
        examples.append({
            "activity_log": (item.get("activity_log") or "")[:max_chars],
            "lesson_learned": (item.get("lesson_learned") or "")[:max_chars],
            "obstacles": (item.get("obstacles") or "")[:max_chars],
        })
    return examples


def build_prompt(user_input: str, examples: list) -> str:
    parts = []

    if examples:
        parts.append(
            "Berikut contoh daily log yang sudah pernah ditulis. Pakai sebagai "
            "acuan gaya dan struktur, bukan untuk disalin isinya:\n"
        )
        for idx, ex in enumerate(examples, 1):
            parts.append(
                f"--- Contoh {idx} ---\n"
                f"activity_log:\n{ex['activity_log']}\n\n"
                f"lesson_learned:\n{ex['lesson_learned']}\n\n"
                f"obstacles:\n{ex['obstacles']}\n"
            )

    parts.append(
        "Sekarang tulis daily log baru berdasarkan catatan pengguna berikut.\n\n"
        f"Catatan pengguna:\n{user_input}\n\n"
        "Keluarkan JSON dengan tiga kunci: activity_log, lesson_learned, obstacles."
    )
    return "\n".join(parts)


def call_gemini(prompt: str) -> dict:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum diisi di .env.")

    model = (os.getenv("GEMINI_MODEL") or "gemini-2.0-flash").strip()
    url = GEMINI_ENDPOINT.format(model=model)

    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }

    res = requests.post(
        url,
        params={"key": api_key},
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )

    if res.status_code != 200:
        raise RuntimeError(f"Gemini HTTP {res.status_code}: {res.text[:400]}")

    data = res.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini tidak mengembalikan kandidat: {json.dumps(data)[:400]}")

    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    if not text:
        raise RuntimeError("Respons Gemini kosong.")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Respons Gemini bukan JSON valid: {e}\n{text[:400]}")

    for key in ("activity_log", "lesson_learned", "obstacles"):
        if not str(parsed.get(key) or "").strip():
            raise RuntimeError(f"Field '{key}' kosong pada respons Gemini.")

    return {
        "activity_log": parsed["activity_log"].strip(),
        "lesson_learned": parsed["lesson_learned"].strip(),
        "obstacles": parsed["obstacles"].strip(),
    }


def build_payload(target_date: str, generated: dict, status: str = "PRESENT") -> dict:
    return {
        "date": target_date,
        "status": status,
        "activity_log": generated["activity_log"],
        "lesson_learned": generated["lesson_learned"],
        "obstacles": generated["obstacles"],
    }


def print_preview(payload: dict) -> None:
    print("\n" + "=" * 62)
    print(f"PREVIEW  |  tanggal: {payload['date']}  |  status: {payload['status']}")
    print("=" * 62)
    for key in ("activity_log", "lesson_learned", "obstacles"):
        print(f"\n[{key}]")
        print(payload[key] or "(kosong)")
    print("\n" + "=" * 62)


# Header persis seperti request browser pada endpoint attendances/with-daily-log
SUBMIT_HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.6",
    "content-type": "application/json",
    "priority": "u=1, i",
}


def submit_payload(payload: dict):
    """
    Kirim daily log ke MagangHub.

    Mengembalikan (ok: bool, message: str) agar UI dapat menampilkan status
    yang jelas tanpa harus membaca terminal.
    """
    url = f"{CONFIG['MONEV_API_BASE']}/attendances/with-daily-log"

    # Urutan & nama field mengikuti contoh request browser
    body = {
        "date": payload["date"],
        "status": payload.get("status") or "PRESENT",
        "activity_log": payload["activity_log"],
        "lesson_learned": payload.get("lesson_learned", ""),
        "obstacles": payload.get("obstacles", ""),
    }

    print(f"POST {url}")
    print(f"body: {json.dumps(body, ensure_ascii=False)[:300]}...")

    try:
        res = fetch_with_auto_refresh(
            "POST", url, params=body, extra_headers=SUBMIT_HEADERS
        )
    except Exception as e:
        msg = f"Gagal terhubung ke server: {e}"
        print(msg)
        return False, msg

    if res.status_code in (200, 201):
        msg = f"Berhasil disimpan (HTTP {res.status_code})."
        print(msg)
        return True, msg

    # --- Terjemahkan kode error menjadi petunjuk yang bisa ditindaklanjuti
    snippet = (res.text or "")[:400]
    if res.status_code == 401:
        msg = "Gagal (401): sesi login kedaluwarsa. Jalankan login_browser.py lalu coba lagi."
    elif res.status_code == 403:
        msg = "Gagal (403): FRONTEND_BUILD_ID usang. Perbarui nilainya di .env."
    elif res.status_code == 422:
        msg = "Gagal (422): format data ditolak server. Periksa tanggal dan status."
    elif res.status_code == 409:
        msg = "Gagal (409): daily log untuk tanggal ini kemungkinan sudah ada."
    elif res.status_code >= 500:
        msg = f"Gagal ({res.status_code}): server MagangHub sedang bermasalah."
    else:
        msg = f"Gagal (HTTP {res.status_code})."

    print(msg)
    print(f"Respons server: {snippet}")
    return False, msg


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate daily log via Gemini lalu (opsional) kirim ke MagangHub."
    )
    parser.add_argument("notes", nargs="*", help="Catatan aktivitas harian Anda")
    parser.add_argument("--date", help="Tanggal target (YYYY-MM-DD), default hari ini WIB")
    parser.add_argument(
        "--submit", action="store_true",
        help="Kirim ke server. Tanpa flag ini hanya menampilkan preview.",
    )
    parser.add_argument("--examples", type=int, default=6, help="Jumlah contoh few-shot")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    tz = pytz.timezone("Asia/Jakarta")
    today = datetime.now(tz).date()
    target_date = args.date or today.isoformat()

    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print(f"Tanggal '{target_date}' tidak valid. Gunakan format YYYY-MM-DD.")
        return 1

    if target_date > today.isoformat():
        print(f"Peringatan: {target_date} berada di masa depan (hari ini {today}).")

    notes = " ".join(args.notes).strip()
    if not notes:
        print("Tuliskan aktivitas hari ini (akhiri dengan baris kosong / Ctrl+D):\n")
        notes = sys.stdin.read().strip()

    if not notes:
        print("Catatan kosong. Dibatalkan.")
        return 1

    examples = load_corpus(max_examples=args.examples)
    print(f"Few-shot: {len(examples)} contoh dari korpus.")

    prompt = build_prompt(notes, examples)

    try:
        generated = call_gemini(prompt)
    except Exception as e:
        print(f"\nGagal generate: {e}")
        return 1

    payload = build_payload(target_date, generated)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Draft disimpan ke {OUTPUT_FILE}")

    print_preview(payload)

    if not args.submit:
        print("Mode preview: tidak ada data yang dikirim.")
        print(f"Untuk mengirim: python gemini_helper.py \"...\" --date {target_date} --submit")
        return 0

    load_token_data()
    ok, message = submit_payload(payload)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())