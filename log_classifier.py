"""
log_classifier.py — Mempelajari activity_logs.json dan mengelompokkannya.

Dua sumbu klasifikasi:
  1. TIPE_HARI   : LIBUR, MASUK_PAGI, MASUK_SIANG, BELAJAR_MANDIRI, TIDAK_JELAS
  2. TOPIK_KERJA : kategori bidang pekerjaan (jaringan, hardware, server, dst.)

Output: classification_summary.json (ringkasan) + stdout (laporan teks).

Pemakaian:
    python log_classifier.py
    python log_classifier.py --json out.json --verbose
"""
import os
import re
import sys
import json
import argparse
from datetime import datetime
from collections import Counter, OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(BASE_DIR, "activity_logs.json")
DEFAULT_OUTPUT = os.path.join(BASE_DIR, "classification_summary.json")

# ============================================================
# KONFIGURASI KLASIFIKASI
# ============================================================

# Batas jam WIB. Mulai kerja normal 08:00.
BATAS_PAGI_H = 8      # mulai < 08:xx  -> MASUK_PAGI (termasuk 07:xx lebih awal)
BATAS_SIANG_H = 12    # 08:xx - 11:xx -> MASUK_PAGI ; >= 12:xx -> MASUK_SIANG
JAM_KERJA_PENUH_H = 17

KATA_LIBUR = [
    "hari libur", "libur/off", "off operasional", "libur pengganti",
    "day off", "cuti", "tanggal merah", "libur nasional",
]

# Marker aktivitas tanpa penanda waktu (belajar/studi mandiri)
KATA_BELAJAR = [
    "studi konsep", "pembelajaran", "mempelajari", "belajar mandiri",
    "aktivitas pembelajaran", "eksplorasi konsep", "riset",
]

# Topik kerja: urutan penting (lebih spesifik didahulukan)
TOPIK_KEYWORDS = OrderedDict([
    ("Jaringan & Infrastruktur", [
        "jaringan", "kabel", "lan", "vlan", "switch", "router", "firewall",
        "wifi", "wi-fi", "koneksi", "ip address", "rj45", "patch",
    ]),
    ("Server & Virtualisasi", [
        "server", "docker", "container", "kontainer", "nginx", "linux",
        "virtualisasi", "vm", "uptime", "domain", "ssl", "https", "proxy",
        "media server", "rtsp", "streaming", "zoneminder",
    ]),
    ("CCTV & Monitoring", [
        "cctv", "kamera", "kamera pengawas", "monitoring", "ip verify",
        "network monitoring", "pemantauan",
    ]),
    ("Hardware & Periferal", [
        "printer", "hardware", "perangkat keras", "mesin apm", "apm",
        "dot matrix", "periferal", "peripheral", "monitor", "pc", "komputer",
        "listrik", "kelistrikan", "kabel jaringan",
    ]),
    ("Software & Otomatisasi", [
        "powershell", "script", "otomatisasi", "aplikasi", "web", "iot",
        "antarmuka", "interface", "ui", "ux", "program", "kode", "aplikasi",
        "integrasi", "api",
    ]),
    ("Administrasi & Aset IT", [
        "aset", "inventaris", "administrasi", "data entry", "pendataan",
        "digitalisasi", "audit", "akun", "lisensi", "helpdesk", "layanan",
    ]),
])

KATEGORI_TOPIK = list(TOPIK_KEYWORDS.keys()) + ["Lain-lain"]

# ============================================================
# EKSTRAKSI WAKTU
# ============================================================

POLA_WAKTU = re.compile(r"(\d{1,2})[.:](\d{2})")
POLA_RENTANG = re.compile(
    r"(\d{1,2})[.:](\d{2})\s*(?:-|–|s/d|s\.d\.|\u2013|\u2014)\s*"
    r"(\d{1,2})[.:](\d{2})",
    re.IGNORECASE,
)


def _to_menit(jam: str, menit: str):
    """Konversi jam:menit ke total menit sejak 00:00. None bila di luar rentang wajar."""
    try:
        h, m = int(jam), int(menit)
    except (TypeError, ValueError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return h * 60 + m


def ekstrak_waktu(teks: str) -> dict:
    """
    Ambil jam mulai & jam selesai dari activity_log.

    Mengembalikan dict:
      mulai_menit, mulai_str, selesai_menit, selesai_str, durasi_menit
    Nilai None bila tidak terdeteksi.
    """
    out = {
        "mulai_menit": None, "mulai_str": None,
        "selesai_menit": None, "selesai_str": None,
        "durasi_menit": None,
    }
    if not teks:
        return out

    # 1) Prioritas rentang eksplisit: "08.00 - 10.00 WIB"
    m = POLA_RENTANG.search(teks)
    if m:
        a = _to_menit(m.group(1), m.group(2))
        b = _to_menit(m.group(3), m.group(4))
        if a is not None:
            out["mulai_menit"] = a
            out["mulai_str"] = f"{a // 60:02d}:{a % 60:02d}"
        if b is not None:
            out["selesai_menit"] = b
            out["selesai_str"] = f"{b // 60:02d}:{b % 60:02d}"
        if a is not None and b is not None:
            dur = b - a
            # Rentang lintas tengah malam tidak wajar untuk daily log -> abaikan
            out["durasi_menit"] = dur if dur > 0 else None
        return out

    # 2) Ambil timestamp tunggal paling awal (baris per baris, urut dokumen)
    for baris in teks.splitlines():
        mm = POLA_WAKTU.search(baris)
        if not mm:
            continue
        a = _to_menit(mm.group(1), mm.group(2))
        # Lewati angka yang jelas bukan jam operasional (mis. "1.5 liter")
        if a is None or a > 22 * 60:
            continue
        out["mulai_menit"] = a
        out["mulai_str"] = f"{a // 60:02d}:{a % 60:02d}"
        break

    return out


# ============================================================
# KLASIFIKASI
# ============================================================

def _teks_gabung(item: dict) -> str:
    return " ".join([
        str(item.get("activity_log") or ""),
        str(item.get("lesson_learned") or ""),
        str(item.get("obstacles") or ""),
    ]).lower()


def klasifikasi_tipe_hari(item: dict) -> tuple:
    """Kembalikan (tipe_hari, alasan)."""
    teks = _teks_gabung(item)
    waktu = ekstrak_waktu(item.get("activity_log") or "")
    mulai = waktu["mulai_menit"]

    # Libur menang atas segalanya
    for kata in KATA_LIBUR:
        if kata in teks:
            return "LIBUR", f"kata kunci '{kata}'"

    # Ada rentang penuh 08.00-17.00 yang isinya libur sudah tertangkap di atas.
    # Belajar mandiri: tanpa penanda waktu sebenarnya
    if mulai is None:
        ada_belajar = any(k in teks for k in KATA_BELAJAR)
        return ("BELAJAR_MANDIRI", "tanpa penanda waktu") if ada_belajar \
            else ("TIDAK_JELAS", "tanpa penanda waktu & kata kunci dikenal")

    mulai_h = mulai // 60
    if mulai_h < BATAS_PAGI_H:
        return "MASUK_PAGI", f"mulai {waktu['mulai_str']} (sebelum 08:00)"
    if mulai_h < BATAS_SIANG_H:
        return "MASUK_PAGI", f"mulai {waktu['mulai_str']}"
    if mulai_h < JAM_KERJA_PENUH_H:
        return "MASUK_SIANG", f"mulai {waktu['mulai_str']} (setelah 12:00)"
    return "MASUK_SIANG", f"mulai {waktu['mulai_str']} (sore)"


def klasifikasi_topik(item: dict) -> tuple:
    """
    Kembalikan (list_topik, skor_dict).
    Satu entri bisa punya >1 topik karena pekerjaan IT sering tumpang tindih.
    """
    teks = _teks_gabung(item)
    skor = {}
    for topik, kata_list in TOPIK_KEYWORDS.items():
        n = sum(teks.count(k) for k in kata_list)
        if n:
            skor[topik] = n
    if not skor:
        return ["Lain-lain"], {}
    return list(skor.keys()), skor


POLA_KATEGORI = re.compile(r"^\s*([^:\n]{3,60}):")


def _kategori_lesson(teks: str) -> str:
    """Ambil prefix kategori sebelum titik dua pada lesson_learned."""
    if not teks:
        return ""
    m = POLA_KATEGORI.match(teks.strip())
    return m.group(1).strip() if m else ""


def klasifikasi_satu(item: dict) -> dict:
    tipe, alasan = klasifikasi_tipe_hari(item)

    # Hari libur tidak punya pekerjaan teknis; kata kunci pada obstacles
    # ("sistem stabil", "tidak ada kendala jaringan") tidak boleh dihitung topik.
    if tipe == "LIBUR":
        topik, skor = [], {}
    else:
        topik, skor = klasifikasi_topik(item)

    waktu = ekstrak_waktu(item.get("activity_log") or "")
    tanggal = item.get("date") or ""
    try:
        dow = datetime.strptime(tanggal, "%Y-%m-%d").strftime("%A")
    except ValueError:
        dow = ""
    panjang = len((item.get("activity_log") or "").strip())
    return {
        "date": tanggal,
        "day_of_week": dow,
        "tipe_hari": tipe,
        "alasan_tipe": alasan,
        "topik": topik,
        "skor_topik": skor,
        "jam_mulai": waktu["mulai_str"],
        "jam_selesai": waktu["selesai_str"],
        "durasi_menit": waktu["durasi_menit"],
        "panjang_teks": panjang,
        "kategori_lesson": _kategori_lesson(item.get("lesson_learned") or ""),
    }


# ============================================================
# AGREGASI
# ============================================================

def _statistik_durasi(menit_list) -> dict:
    bersih = [m for m in menit_list if m]
    if not bersih:
        return {"count": 0, "min": None, "max": None, "rata_rata": None}
    return {
        "count": len(bersih),
        "min": min(bersih),
        "max": max(bersih),
        "rata_rata": round(sum(bersih) / len(bersih)),
    }


def rangkum(hasil: list, sumber: dict) -> dict:
    tipe_counter = Counter(h["tipe_hari"] for h in hasil)
    topik_counter = Counter(t for h in hasil for t in h["topik"])
    dow_counter = Counter(h["day_of_week"] for h in hasil if h["day_of_week"])

    per_tipe = {}
    for h in hasil:
        per_tipe.setdefault(h["tipe_hari"], []).append(h)

    rincian_tipe = {}
    for tipe, items in per_tipe.items():
        topik_dalam = Counter(t for h in items for t in h["topik"])
        mulai_list = []
        for h in items:
            if h["jam_mulai"]:
                j, mnt = h["jam_mulai"].split(":")
                mulai_list.append(int(j) * 60 + int(mnt))
        rincian_tipe[tipe] = {
            "jumlah": len(items),
            "tanggal": sorted(h["date"] for h in items if h["date"]),
            "topik_dominan": topik_dalam.most_common(3),
            "statistik_jam_mulai": _statistik_durasi(mulai_list),
        }

    return {
        "sumber_file": sumber.get("_file"),
        "periode": sumber.get("period"),
        "total_entri": len(hasil),
        "distribusi_tipe_hari": tipe_counter.most_common(),
        "distribusi_topik": topik_counter.most_common(),
        "distribusi_hari": dow_counter.most_common(),
        "statistik_durasi_menit": _statistik_durasi([h["durasi_menit"] for h in hasil]),
        "rincian_per_tipe": rincian_tipe,
        "rincian_per_entri": hasil,
    }


# ============================================================
# LAPORAN TEKS
# ============================================================

def cetak_laporan(ringkas: dict, verbose: bool = False) -> None:
    print("=" * 64)
    print("KLASIFIKASI ACTIVITY LOGS")
    print("=" * 64)
    periode = ringkas.get("periode") or {}
    print(f"Periode     : {periode.get('start')} .. {periode.get('end')}")
    print(f"Total entri : {ringkas['total_entri']}")
    print()

    print("-- Distribusi Tipe Hari " + "-" * 40)
    for tipe, n in ringkas["distribusi_tipe_hari"]:
        print(f"  {tipe:<16} {n:>3}")
    print()

    print("-- Distribusi Topik Kerja " + "-" * 38)
    for topik, n in ringkas["distribusi_topik"]:
        print(f"  {topik:<32} {n:>3}")
    print()

    print("-- Distribusi Hari (day of week) " + "-" * 32)
    for dow, n in ringkas["distribusi_hari"]:
        print(f"  {dow:<16} {n:>3}")
    print()

    sd = ringkas["statistik_durasi_menit"]
    if sd["count"]:
        print("-- Durasi Kerja " + "-" * 47)
        print(f"  terdeteksi : {sd['count']} entri")
        print(f"  min/maks   : {sd['min']} / {sd['max']} menit")
        print(f"  rata-rata  : {sd['rata_rata']} menit")
        print()

    print("-- Rincian per Tipe Hari " + "-" * 39)
    for tipe, info in ringkas["rincian_per_tipe"].items():
        print(f"\n  [{tipe}]  {info['jumlah']} entri")
        topik_str = ", ".join(f"{t}({n})" for t, n in info["topik_dominan"]) or "-"
        print(f"    topik dominan : {topik_str}")
        print(f"    tanggal       : {', '.join(info['tanggal'])}")

    if verbose:
        print("\n-- Rincian per Entri " + "-" * 43)
        for h in ringkas["rincian_per_entri"]:
            jam = f"{h['jam_mulai'] or '--:--'}-{h['jam_selesai'] or '--:--'}"
            print(f"  {h['date']}  {h['tipe_hari']:<16} {jam:<12} "
                  f"{','.join(h['topik'])}")

    insp = ringkas.get("insight") or {}
    if insp:
        print("\n-- Insight untuk AI/GUI " + "-" * 40)
        print(f"  tipe dominan      : {', '.join(insp.get('tipe_hari_dominan') or [])}")
        print(f"  jam mulai umum    : {', '.join(insp.get('jam_mulai_umum') or []) or '-'}")
        print(f"  durasi rata-rata  : {insp.get('durasi_menit_rata_rata')} menit")
        print(f"  topik dominan     : {', '.join(insp.get('topik_dominan') or [])}")
        print(f"  gaya waktu        : {insp.get('gaya_penanda_waktu')}")
        kat = insp.get("kategori_pelajaran_lazim") or []
        if kat:
            print(f"  kategori pelajaran: {'; '.join(kat)}")
    print()


# ============================================================
# INSIGHT UNTUK AI / GUI
# ============================================================

def buat_insight(ringkas: dict) -> dict:
    """
    Ringkasan padat untuk prompt Gemini & panel saran GUI.
    Hanya fakta terukur dari riwayat, tanpa teks mentah.
    """
    entri = ringkas.get("rincian_per_entri") or []
    kerja = [h for h in entri if h["tipe_hari"] != "LIBUR"]

    # Jam mulai paling umum pada hari kerja
    jam_counter = Counter(h["jam_mulai"] for h in kerja if h["jam_mulai"])
    sd = ringkas.get("statistik_durasi_menit") or {}

    # Topik dominan
    topik = [t for t, _ in (ringkas.get("distribusi_topik") or [])[:4]]

    # Tipe hari dominan
    tipe = [t for t, _ in (ringkas.get("distribusi_tipe_hari") or [])[:3]]

    # Kategori lesson_learned yang lazim (prefix sebelum titik dua)
    kategori = Counter()
    for h in entri:
        p = (h.get("kategori_lesson") or "").strip()
        if p:
            kategori[p] += 1

    return {
        "total_entri": ringkas.get("total_entri", 0),
        "tipe_hari_dominan": tipe,
        "jam_mulai_umum": [j for j, _ in jam_counter.most_common(3)],
        "durasi_menit_rata_rata": sd.get("rata_rata"),
        "durasi_menit_min_maks": [sd.get("min"), sd.get("max")],
        "topik_dominan": topik,
        "gaya_penanda_waktu": "24 jam, format 'HH.MM - HH.MM: deskripsi'",
        "kategori_pelajaran_lazim": [k for k, _ in kategori.most_common(5)],
    }


def saran_cepat(date_str: str, ringkas: dict, jam_mulai: str = None) -> list:
    """
    Saran konkret untuk pengisian cepat di GUI.
    Kembalikan list dict {tipe, pesan}.
    """
    saran = []
    entri = ringkas.get("rincian_per_entri") or []

    # Sudah pernah diisi?
    sama = [h for h in entri if h["date"] == date_str]
    if sama:
        h = sama[0]
        saran.append({
            "tipe": "peringatan",
            "pesan": f"Tanggal {date_str} sudah ada di riwayat "
                     f"({h['tipe_hari']}, {'/'.join(h['topik']) or 'tanpa topik'}).",
        })

    dow = ""
    try:
        dow = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
    except ValueError:
        saran.append({"tipe": "error", "pesan": "Format tanggal harus YYYY-MM-DD."})
        return saran

    if dow in ("Saturday", "Sunday"):
        saran.append({
            "tipe": "info",
            "pesan": f"{date_str} jatuh pada {dow} (akhir pekan). "
                     "Pastikan memang ada jadwal piket.",
        })

    kerja = [h for h in entri if h["tipe_hari"] != "LIBUR" and h["jam_mulai"]]
    if kerja:
        jam_counter = Counter(h["jam_mulai"] for h in kerja)
        umum, n = jam_counter.most_common(1)[0]
        if jam_mulai and jam_mulai != umum:
            saran.append({
                "tipe": "info",
                "pesan": f"Catatan mulai {jam_mulai}; pola riwayat biasanya {umum} "
                         f"({n} entri).",
            })
        elif not jam_mulai:
            saran.append({
                "tipe": "arahan",
                "pesan": f"Awali catatan dengan '{umum} - ' mengikuti pola riwayat.",
            })

    topik = [t for t, _ in (ringkas.get("distribusi_topik") or [])[:4]]
    if topik:
        saran.append({
            "tipe": "arahan",
            "pesan": "Topik yang sering Anda kerjakan: " + ", ".join(topik) + ".",
        })

    sd = ringkas.get("statistik_durasi_menit") or {}
    if sd.get("rata_rata"):
        saran.append({
            "tipe": "arahan",
            "pesan": f"Durasi kerja tercatat biasanya ±{sd['rata_rata']} menit "
                     f"(rentang {sd['min']}–{sd['max']} menit).",
        })

    insp = ringkas.get("insight") or {}
    kat = insp.get("kategori_pelajaran_lazim") or []
    if kat:
        saran.append({
            "tipe": "arahan",
            "pesan": "Kategori lesson_learned lazim: " + "; ".join(kat[:3]) + ".",
        })

    return saran


# ============================================================
# SELF-CHECK
# ============================================================

def _self_check():
    """Verifikasi aturan klasifikasi & parser waktu. Jalankan: python log_classifier.py --self-check"""
    kasus = [
        # (activity_log, tipe_diharapkan)
        ("08.00 - 10.00 WIB: Pendampingan pasien.", "MASUK_PAGI"),
        ("07.50 - 08.30: Briefing pagi.", "MASUK_PAGI"),
        ("13.30 - 14.00: Maintenance printer.", "MASUK_SIANG"),
        ("08.00 - 17.00: Hari libur/off operasional pengganti.", "LIBUR"),
        ("Aktivitas pembelajaran berfokus pada studi konsep arsitektur jaringan.", "BELAJAR_MANDIRI"),
        ("12.00 - 13.00: Istirahat dan lanjut kerja.", "MASUK_SIANG"),
    ]
    gagal = 0
    for teks, harap in kasus:
        item = {"date": "2026-10-15", "activity_log": teks,
                "lesson_learned": "", "obstacles": ""}
        dapat, alasan = klasifikasi_tipe_hari(item)
        ok = dapat == harap
        gagal += 0 if ok else 1
        print(f"  [{'OK ' if ok else 'GAGAL'}] {harap:<15} -> {dapat:<15} ({alasan})")

    # libur tidak boleh punya topik
    item_libur = {"date": "2026-10-15",
                  "activity_log": "08.00 - 17.00: Hari libur/off operasional.",
                  "lesson_learned": "Manajemen Waktu: koordinasi jadwal shift.",
                  "obstacles": "Tidak ada kendala jaringan karena sistem stabil."}
    h = klasifikasi_satu(item_libur)
    ok = h["tipe_hari"] == "LIBUR" and h["topik"] == []
    gagal += 0 if ok else 1
    print(f"  [{'OK ' if ok else 'GAGAL'}] LIBUR tanpa topik -> tipe={h['tipe_hari']} topik={h['topik']}")

    # parser rentang
    w = ekstrak_waktu("08.00 - 10.30 WIB: kerja")
    ok = w["mulai_str"] == "08:00" and w["selesai_str"] == "10:30" and w["durasi_menit"] == 150
    gagal += 0 if ok else 1
    print(f"  [{'OK ' if ok else 'GAGAL'}] parser rentang -> {w}")

    # timestamp tunggal
    w2 = ekstrak_waktu("Penataan kabel.\n10.30 WIB: Reconnect Wi-Fi.\n13.30: Printer.")
    ok = w2["mulai_str"] == "10:30"
    gagal += 0 if ok else 1
    print(f"  [{'OK ' if ok else 'GAGAL'}] parser timestamp tunggal -> {w2['mulai_str']}")

    print(f"\n{'SEMUA LULUS' if gagal == 0 else f'{gagal} KASUS GAGAL'}")
    return 0 if gagal == 0 else 1


# ============================================================
# ENTRY POINT
# ============================================================

def muat_activity(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} tidak ada. Jalankan 1_ambil_data_log.py lebih dahulu."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):  # dukung format legacy
        data = {"activities": data, "total_logs": len(data)}
    data["_file"] = os.path.basename(path)
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Klasifikasi activity_logs.json ke kategori tipe hari & topik kerja."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="File activity_logs.json")
    parser.add_argument("--json", dest="json_out", default=DEFAULT_OUTPUT,
                        help="Tulis ringkasan JSON ke path ini")
    parser.add_argument("--verbose", action="store_true", help="Tampilkan rincian per entri")
    parser.add_argument("--no-save", action="store_true", help="Jangan tulis file JSON")
    parser.add_argument("--self-check", action="store_true",
                        help="Verifikasi aturan klasifikasi lalu keluar")
    args = parser.parse_args(argv)

    if args.self_check:
        return _self_check()

    data = muat_activity(args.input)
    kegiatan = data.get("activities") or []
    if not kegiatan:
        print("Tidak ada aktivitas pada file sumber.")
        return 1

    hasil = [klasifikasi_satu(item) for item in kegiatan]
    ringkas = rangkum(hasil, data)
    ringkas["insight"] = buat_insight(ringkas)

    cetak_laporan(ringkas, verbose=args.verbose)

    if not args.no_save:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(ringkas, f, indent=2, ensure_ascii=False)
        print(f"Ringkasan disimpan: {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
