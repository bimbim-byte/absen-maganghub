"""
env_loader.py — Loader .env tunggal untuk seluruh proyek.
Gunakan: from env_loader import load_env; load_env()
"""
import os

def load_env() -> None:
    """Muat variabel dari .env ke os.environ (fallback jika python-dotenv tidak ada)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
