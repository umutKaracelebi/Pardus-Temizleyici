"""
Pardus Sistem Temizleyici — Temizlik geçmişi

Her temizlik işlemi JSON formatında kaydedilir.
Sonuçlar sayfasında toplam istatistik gösterilir.
"""

import os
import json
import time


HISTORY_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "pardus-temizleyici"
)
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_clean_record(clean_results):
    """Temizlik sonucunu kaydet."""
    _ensure_dir()

    record = {
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "categories": {},
        "total_freed": 0,
    }

    for cat_id, result in clean_results.items():
        if result.success and result.freed_size > 0:
            record["categories"][cat_id] = result.freed_size
            record["total_freed"] += result.freed_size

    if record["total_freed"] == 0:
        return

    history = load_history()
    history.append(record)

    # Son 100 kayıt tut
    history = history[-100:]

    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except (OSError, IOError):
        pass


def load_history():
    """Geçmişi yükle."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def get_stats():
    """Toplam istatistikleri döndürür."""
    history = load_history()

    total_freed = sum(r.get("total_freed", 0) for r in history)
    total_sessions = len(history)
    last_clean = history[-1].get("date", "—") if history else "—"

    # Kategori bazında toplam
    cat_totals = {}
    for record in history:
        for cat_id, size in record.get("categories", {}).items():
            cat_totals[cat_id] = cat_totals.get(cat_id, 0) + size

    return {
        "total_freed": total_freed,
        "total_sessions": total_sessions,
        "last_clean": last_clean,
        "category_totals": cat_totals,
    }
