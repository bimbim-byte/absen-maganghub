import os
import json
import pytz
from datetime import datetime, date, timedelta

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

from main import CONFIG, load_token_data, get_user_info, fetch_with_auto_refresh

OUTPUT_FILE = os.path.join(BASE_DIR, "activity_logs.json")


MAX_PAGES = 20


def _month_env(name: str, default: date) -> date:
    """
    Baca bulan dari env dengan format YYYY-MM (contoh: 2026-10).
    Mengembalikan tanggal 1 dari bulan tersebut.
    Jika kosong / tidak valid, pakai `default`.
    """
    raw = (os.getenv(name) or "").strip()
    if not raw:
        print(f"{name} belum diisi di .env, memakai {default.strftime('%Y-%m')}.")
        return default.replace(day=1)

    try:
        year_str, month_str = raw.split("-")[:2]
        return date(int(year_str), int(month_str), 1)
    except (ValueError, TypeError):
        print(f"Nilai {name}='{raw}' tidak valid (format YYYY-MM). Memakai {default.strftime('%Y-%m')}.")
        return default.replace(day=1)


def add_months(ref: date, delta: int) -> date:
    """Geser sejumlah bulan, hasil selalu tanggal 1."""
    year, month = ref.year, ref.month + delta
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, 1)


def last_day_of(ref: date) -> date:
    return add_months(ref, 1) - timedelta(days=1)


def resolve_range(today: date):
    """
    Rentang diambil dari .env:
        MULAI_BULAN=2026-10   -> tanggal 1 bulan tersebut
        AKHIR_BULAN=2026-12   -> hari terakhir bulan tersebut

    Aturan pemotongan:
    - Jika AKHIR_BULAN melewati bulan berjalan, potong ke bulan berjalan.
    - Jika akhirnya jatuh di bulan berjalan, potong lagi ke hari ini
      (tanggal masa depan tidak pernah punya log).
    - Jika MULAI_BULAN > AKHIR_BULAN, rentang dikosongkan.
    """
    current_month = today.replace(day=1)

    start = _month_env("MULAI_BULAN", current_month)
    end_month = _month_env("AKHIR_BULAN", current_month)

    # Jangan pernah melewati bulan yang sedang berjalan
    if end_month > current_month:
        end_month = current_month

    end = last_day_of(end_month)
    if end_month == current_month:
        end = min(end, today)

    if start > end:
        print("MULAI_BULAN berada setelah batas AKHIR_BULAN/bulan sistem. Tidak ada data diambil.")
        return start, start - timedelta(days=1)

    return start, end


def iter_months(start: date, end: date):
    """Yield tanggal 1 untuk setiap bulan yang beririsan dengan [start, end]."""
    current = start.replace(day=1)
    while current <= end:
        yield current
        current = add_months(current, 1)


def _fetch_page(participant_id: str, anchor_date: str, page: int, limit: int):
    """
    Satu request ke /daily-logs.

    Catatan penting: parameter `date` pada API ini TIDAK memfilter per hari
    (mis. date=2026-10-01 tetap mengembalikan log tanggal 2026-10-23).
    Nilainya hanya dipakai sebagai anchor periode, jadi pemfilteran
    tanggal dilakukan di sisi klien.
    """
    url = f"{CONFIG['MONEV_API_BASE']}/daily-logs"
    params = {
        "date": anchor_date,
        "participant_id": participant_id,
        "limit": limit,
        "page": page,
    }
    res = fetch_with_auto_refresh("GET", url, params=params)
    if res.status_code != 200:
        print(f"[{anchor_date} p{page}] HTTP {res.status_code}, berhenti.")
        return None
    payload = res.json()
    items = [i for i in payload.get("data", []) if isinstance(i, dict) and i]
    total = payload.get("total") or 0
    return items, total


def fetch_logs_for_month(participant_id: str, month_start: date, limit: int = None):
    """Ambil seluruh daily-logs untuk satu bulan (dengan pagination)."""
    limit = limit or CONFIG["LIMIT"]
    anchor = month_start.replace(day=1).isoformat()
    results = []

    for page in range(MAX_PAGES):
        try:
            page_result = _fetch_page(participant_id, anchor, page, limit)
        except Exception as e:
            print(f"[{anchor} p{page}] Error fetching logs: {e}")
            break

        if page_result is None:
            break

        items, total = page_result
        results.extend(items)

        if not items or len(items) < limit or (total and len(results) >= total):
            break

    return results


def clean_text(value) -> str:
    """Normalisasi nilai teks dari API: buang spasi tepi, pertahankan newline internal."""
    if not isinstance(value, str):
        return ""
    return value.strip()


def collect_activity_logs():
    load_token_data()

    participant_id = get_user_info().get("participant_id")
    if not participant_id:
        print("Participant ID not found. Aborting.")
        return None

    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    start, end = resolve_range(now.date())

    print(f"Mengambil daily log {start} .. {end}")
    print(f"Peserta: {participant_id}")

    collected = {}
    seen_ids = set()

    for month_start in iter_months(start, end):
        logs = fetch_logs_for_month(participant_id, month_start)
        print(f"  {month_start.strftime('%Y-%m')}: {len(logs)} entri")

        for log in logs:
            log_id = log.get("id")
            if log_id in seen_ids:
                continue
            seen_ids.add(log_id)

            log_date = (log.get("date") or "")[:10]
            if not (start.isoformat() <= log_date <= end.isoformat()):
                continue

            activity = clean_text(log.get("activity_log"))
            if not activity:
                continue

            # Urutan kunci dipertahankan sesuai permintaan:
            # activity_log -> lesson_learned -> obstacles
            collected[log_date] = {
                "id": log_id,
                "date": log_date,
                "activity_log": activity,
                "lesson_learned": clean_text(log.get("lesson_learned")),
                "obstacles": clean_text(log.get("obstacles")),
            }

    ordered = [collected[k] for k in sorted(collected)]

    result = {
        "participant_id": participant_id,
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "total_logs": len(ordered),
        "generated_at": now.isoformat(),
        "activities": ordered,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Selesai. {len(ordered)} activity log disimpan ke {OUTPUT_FILE}")
    return result


if __name__ == "__main__":
    collect_activity_logs()