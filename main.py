import os
import sys
import json
import subprocess
import requests
from datetime import datetime
import pytz

# ============================================================
# HELPER PEMUATAN ENVIRONMENT VARIABLE (.env)
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE_PATH)
except ImportError:
    # Fallback loader jika python-dotenv belum terpasang
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

# ============================================================
# KONFIGURASI UTAMA
# ============================================================
TOKEN_FILE_PATH = os.path.join(BASE_DIR, "token.json")

CONFIG = {
    "TOKEN": "",
    "PARTICIPANT_ID": os.getenv("PARTICIPANT_ID", ""),
    "LIMIT": int(os.getenv("LIMIT", "100")),
    
    # Konfigurasi Telegram Bot
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),

    # Jam operasional pengiriman notifikasi/pengecekan (Format 24 jam)
    "START_HOUR": int(os.getenv("START_HOUR", "1")),
    "END_HOUR": int(os.getenv("END_HOUR", "23")),

    # URL API & WAF Headers
    "MONEV_API_BASE": os.getenv("MONEV_API_BASE", "https://monev-api.maganghub.kemnaker.go.id/api/v1"),
    "FRONTEND_BUILD_ID": os.getenv("FRONTEND_BUILD_ID", "fdce5864ab936c3205233ffc340ba593c0136cd2-production"),
    "USER_AGENT": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"),
    "TOKEN_FILE": TOKEN_FILE_PATH
}

# Session requests untuk menjaga koneksi dan cookie
session = requests.Session()


# ============================================================
# MANAJEMEN PENYIMPANAN TOKEN & COOKIE LOKAL
# ============================================================

def load_token_data():
    """
    Membaca data token dan cookie dari token.json.
    Mendukung format objek baru maupun format list legacy.
    """
    filepath = CONFIG["TOKEN_FILE"]
    if not os.path.exists(filepath):
        print("Token file not found.")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            access_token = data.get("access_token")
            refresh_token = data.get("monev_refresh_token")
            raw_cookies = data.get("cookies", [])

            # Pasang cookies ke requests.Session
            if isinstance(raw_cookies, list):
                for c in raw_cookies:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        domain = c.get("domain", "")
                        path = c.get("path", "/")
                        session.cookies.set(c["name"], c["value"], domain=domain, path=path)
            elif isinstance(raw_cookies, dict):
                for k, v in raw_cookies.items():
                    session.cookies.set(k, v)

            if access_token:
                CONFIG["TOKEN"] = access_token

            return {
                "access_token": access_token,
                "monev_refresh_token": refresh_token,
                "cookies": raw_cookies
            }

        elif isinstance(data, list):
            # Format legacy (array of cookies dari Playwright)
            refresh_token = None
            for c in data:
                if isinstance(c, dict) and "name" in c and "value" in c:
                    if c["name"] == "monev_refresh_token":
                        refresh_token = c["value"]
                    session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""), path=c.get("path", "/"))
            return {
                "access_token": None,
                "monev_refresh_token": refresh_token,
                "cookies": data
            }

    except Exception as e:
        print(f"Error reading token.json: {e}")

    return None


def save_token_data(new_access_token=None, new_refresh_token=None, new_cookies=None):
    """
    Menyimpan atau memperbarui data token ke file token.json
    tanpa menghilangkan cookie atau properti lain yang sudah ada.
    """
    filepath = CONFIG["TOKEN_FILE"]
    data = {}

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if isinstance(existing, dict):
                    data = existing
                elif isinstance(existing, list):
                    data["cookies"] = existing
        except Exception:
            pass

    if new_access_token:
        data["access_token"] = new_access_token
        CONFIG["TOKEN"] = new_access_token

    if new_refresh_token:
        data["monev_refresh_token"] = new_refresh_token

    if new_cookies is not None:
        data["cookies"] = new_cookies

    data["updated_at"] = datetime.now().isoformat()

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Session data saved to token.json.")
    except Exception as e:
        print(f"Error saving token.json: {e}")


# ============================================================
# HEADER BUILDER
# ============================================================

def get_headers(include_auth=True):
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "x-frontend-build-id": CONFIG["FRONTEND_BUILD_ID"],
        "user-agent": CONFIG["USER_AGENT"]
    }
    if include_auth and CONFIG["TOKEN"]:
        token_clean = CONFIG["TOKEN"].replace("Bearer ", "").strip()
        headers["authorization"] = f"Bearer {token_clean}"
    return headers


# ============================================================
# FUNGSI REFRESH TOKEN API & EKSEKUSI GET_COOKIE
# ============================================================

def refresh_token_api():
    """
    Memanggil endpoint /auth/refresh menggunakan cookie monev_refresh_token
    untuk mendapatkan access_token baru secara instan tanpa membuka browser.
    """
    url = f"{CONFIG['MONEV_API_BASE']}/auth/refresh"
    print("Refreshing access token via API...")

    cookie_dict = session.cookies.get_dict()
    refresh_token = cookie_dict.get("monev_refresh_token")
    if not refresh_token:
        token_info = load_token_data()
        if token_info:
            refresh_token = token_info.get("monev_refresh_token")

    if not refresh_token:
        print("Refresh token not found in token.json.")
        return False

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://monev.maganghub.kemnaker.go.id",
        "x-frontend-build-id": CONFIG["FRONTEND_BUILD_ID"],
        "user-agent": CONFIG["USER_AGENT"]
    }

    req_cookies = {"monev_refresh_token": refresh_token}
    if "cf_clearance" in cookie_dict:
        req_cookies["cf_clearance"] = cookie_dict["cf_clearance"]
    if "acw_tc" in cookie_dict:
        req_cookies["acw_tc"] = cookie_dict["acw_tc"]

    try:
        response = requests.post(url, headers=headers, cookies=req_cookies, data=b"", timeout=20)

        if response.status_code in [200, 201]:
            res_data = response.json()
            new_token = res_data.get("access_token")
            if new_token:
                print("Token refreshed successfully.")
                # Periksa apakah ada rotasi refresh token di respon cookie
                rotated_refresh = response.cookies.get("monev_refresh_token")
                save_token_data(new_access_token=new_token, new_refresh_token=rotated_refresh)
                return True
            else:
                print("Refresh response did not return a new token.")
        else:
            print("Failed to refresh token via API.")

    except Exception as e:
        print(f"Error during token refresh: {e}")

    return False


def run_get_cookie_script():
    """
    Menjalankan skrip get_cookie.py untuk membuka browser Playwright,
    mengambil sesi baru secara interaktif, dan memperbarui file token.json.
    """
    print("\nSession expired (401). Opening browser for re-login...")

    script_path = os.path.join(BASE_DIR, "get_cookie.py")
    if not os.path.exists(script_path):
        print("get_cookie.py script not found.")
        return False

    # Use the current Python interpreter (with Playwright installed) to run get_cookie.py
python_bin = sys.executable

    print("Running get_cookie.py...")
    try:
        result = subprocess.run([python_bin, script_path], cwd=BASE_DIR, check=True)
        print("Browser login completed.")

        # Muat ulang token & cookies dari token.json yang baru saja diupdate
        token_info = load_token_data()

        # Jika access_token belum tertangkap langsung tetapi monev_refresh_token baru tersedia, panggil refresh API
        if not CONFIG.get("TOKEN"):
            print("Loading latest access token...")
            refresh_token_api()

        return True
    except subprocess.CalledProcessError as e:
        print("Failed to update session via browser.")
    except Exception as e:
        print(f"Error running get_cookie.py: {e}")

    return False


# ============================================================
# INTEGRASI TELEGRAM API
# ============================================================

def send_telegram_message(message_text, is_silent=False):
    if not CONFIG["TELEGRAM_BOT_TOKEN"] or not CONFIG["TELEGRAM_CHAT_ID"]:
        print("Telegram bot token or chat ID not set in .env.")
        return

    url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
    
    payload = {
        "chat_id": CONFIG["TELEGRAM_CHAT_ID"],
        "text": message_text,
        "parse_mode": "Markdown",
        "disable_notification": is_silent
    }

    try:
        response = session.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent.")
        else:
            print(f"Failed to send Telegram (Status {response.status_code}).")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


# ============================================================
# HELPER FETCH API MONEV (DENGAN AUTO RECOVERY 401)
# ============================================================

def fetch_with_auto_refresh(method, url, params=None):
    """
    Wrapper HTTP Request:
    Jika menerima 401 Unauthorized:
    1. Coba refresh token instan via API (/auth/refresh).
    2. Jika API refresh gagal (sesi mati), jalankan get_cookie.py untuk mengambil sesi baru.
    3. Setelah token.json diperbarui, ulangi request agar mendapatkan respons 200.
    """
    headers = get_headers(include_auth=True)
    if method.upper() == "GET":
        res = session.get(url, headers=headers, params=params, timeout=15)
    else:
        res = session.post(url, headers=headers, json=params, timeout=15)

    if res.status_code == 401:
        print("Session expired (401). Starting recovery...")

        # 1. Coba refresh via API terlebih dahulu
        recovered = refresh_token_api()

        # 2. Jika API refresh gagal, jalankan get_cookie.py
        if not recovered:
            print("Refresh API failed, switching to browser login...")
            if run_get_cookie_script():
                recovered = True

        # 3. Ulangi request dengan token baru jika berhasil diperbarui
        if recovered:
            print("Retrying request with new token...")
            headers = get_headers(include_auth=True)
            if method.upper() == "GET":
                res = session.get(url, headers=headers, params=params, timeout=15)
            else:
                res = session.post(url, headers=headers, json=params, timeout=15)
            if res.status_code == 200:
                print("Session recovered successfully.")

    return res


def get_off_days():
    """Ambil data Day Off Pengguna"""
    url = f"{CONFIG['MONEV_API_BASE']}/users/me"
    try:
        response = fetch_with_auto_refresh("GET", url)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return data.get("off_days", [])
    except Exception as e:
        print(f"Error fetching weekly off days: {e}")
    return []


def get_holiday_info(target_date):
    """Ambil data Hari Libur Nasional"""
    url = f"{CONFIG['MONEV_API_BASE']}/holidays"
    params = {"page": 1, "limit": 100}
    try:
        response = fetch_with_auto_refresh("GET", url, params=params)
        if response.status_code == 200:
            holidays = response.json().get("data", [])
            for h in holidays:
                if h.get("date") == target_date:
                    return h
    except Exception as e:
        print(f"Error fetching national holidays: {e}")
    return None


def fetch_daily_logs(target_date):
    """Ambil Daily Log dari API"""
    url = f"{CONFIG['MONEV_API_BASE']}/daily-logs"
    params = {
        "date": target_date,
        "participant_id": CONFIG["PARTICIPANT_ID"],
        "limit": CONFIG["LIMIT"]
    }
    try:
        response = fetch_with_auto_refresh("GET", url, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("Login session still invalid.")
            send_telegram_message(
                "⚠️ *Sesi Login MagangHub Habis*\n\n"
                "Sesi akun Anda telah kedaluwarsa.\n"
                "Silakan jalankan `python get_cookie.py` di komputer untuk login ulang.",
                is_silent=False
            )
    except Exception as e:
        print(f"Error fetching daily logs: {e}")
    return {"data": []}


def filter_by_date(data, target_date):
    """Filter Log berdasarkan Tanggal Target"""
    logs = data.get("data", [])
    return [item for item in logs if item.get("date") == target_date]


# ============================================================
# FUNGSI UTAMA
# ============================================================

def check_daily_log_job():
    # 1. Load Token & Cookie Terakhir dari File token.json
    load_token_data()

    # Jika belum ada token sama sekali, coba refresh atau jalankan get_cookie
    if not CONFIG.get("TOKEN"):
        print("No access token. Obtaining new token...")
        if not refresh_token_api():
            run_get_cookie_script()

    # 2. Selalu lakukan request ke web API terlebih dahulu
    print("Checking session and schedule with MagangHub...")
    off_days = get_off_days()

    # 3. Ambil Waktu Saat Ini di WIB (Asia/Jakarta)
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    
    today_str = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    day_name = now.strftime("%A").upper()

    HARI_ID = {
        "MONDAY": "Senin", "TUESDAY": "Selasa", "WEDNESDAY": "Rabu",
        "THURSDAY": "Kamis", "FRIDAY": "Jumat", "SATURDAY": "Sabtu", "SUNDAY": "Minggu"
    }
    nama_hari = HARI_ID.get(day_name, day_name)

    print(f"\nChecking attendance: {nama_hari}, {today_str} ({now.strftime('%H:%M')} WIB)")

    # 4. Cek Jam Operasional
    if current_hour < CONFIG["START_HOUR"] or current_hour > CONFIG["END_HOUR"]:
        print("Outside operational hours. Skipping check.")
        return

    # 5. Jalankan kode dengan normal jika dalam jam operasional
    try:
        # Cek Day Off (Hari Libur Mingguan, misal SATURDAY / SUNDAY)
        if day_name in off_days:
            msg = (
                f"🏖️ *Info Libur Mingguan*\n\n"
                f"Hari ini (*{nama_hari}, {today_str}*) adalah hari libur mingguan.\n"
                f"Selamat beristirahat!"
            )
            print("Today is a weekly holiday.")
            send_telegram_message(msg, is_silent=True)
            return

        # Cek Hari Libur Nasional / Cuti Bersama
        holiday_info = get_holiday_info(today_str)
        if holiday_info:
            nama_libur = holiday_info.get("name", "Hari Libur Nasional")
            msg = (
                f"🎉 *Info Hari Libur Nasional*\n\n"
                f"Hari ini (*{nama_hari}, {today_str}*) adalah hari libur:\n"
                f"*{nama_libur}*\n\n"
                f"Selamat berlibur!"
            )
            print(f"Today is a national holiday: {nama_libur}")
            send_telegram_message(msg, is_silent=True)
            return

        # Cek Daily Log dari Monev API
        daily_logs = fetch_daily_logs(today_str)
        filtered_logs = filter_by_date(daily_logs, today_str)

        if filtered_logs:
            # BILA SUDAH ABSEN
            log_state = filtered_logs[0].get("state", "TERISI")
            msg = (
                f"✅ *Daily Log Sudah Diisi*\n\n"
                f"Tanggal: *{nama_hari}, {today_str}*\n"
                f"Status: *{log_state}*"
            )
            print("Daily log already filled.")
            send_telegram_message(msg, is_silent=True)
        else:
            # BILA BELUM ABSEN
            edit_url = f"https://monev.maganghub.kemnaker.go.id/dashboard/riwayat?date={today_str}&view=edit"
            msg = (
                f"⚠️ *Pengingat Daily Log MagangHub*\n\n"
                f"Anda belum mengisi Daily Log untuk hari ini (*{nama_hari}, {today_str}*).\n\n"
                f"👉 *Silakan isi sekarang melalui tautan berikut:*\n"
                f"{edit_url}"
            )
            print("Daily log not filled. Sending reminder.")
            send_telegram_message(msg, is_silent=False)

    except Exception as e:
        print(f"Error in process: {e}")


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    check_daily_log_job()