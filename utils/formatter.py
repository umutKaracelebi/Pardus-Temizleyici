"""
Pardus Sistem Temizleyici — Dosya boyutu formatlama yardımcıları
"""


def format_size(size_bytes):
    """Bayt cinsinden boyutu okunabilir formata çevirir."""
    if size_bytes < 0:
        return "0 B"
    if size_bytes == 0:
        return "0 B"

    units = [
        (1 << 30, "GB"),
        (1 << 20, "MB"),
        (1 << 10, "KB"),
        (1, "B"),
    ]

    for factor, unit in units:
        if size_bytes >= factor:
            value = size_bytes / factor
            if value >= 100:
                return f"{value:.0f} {unit}"
            elif value >= 10:
                return f"{value:.1f} {unit}"
            else:
                return f"{value:.2f} {unit}"

    return f"{size_bytes} B"


def format_count(count):
    """Dosya sayısını okunabilir formata çevirir."""
    if count >= 1000000:
        return f"{count / 1000000:.1f}M"
    elif count >= 1000:
        return f"{count / 1000:.1f}K"
    return str(count)
