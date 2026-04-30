"""
Pardus Sistem Temizleyici — Sistem bilgisi toplama
"""

import os
import shutil


def get_disk_usage(path="/"):
    """Disk kullanım bilgisini döndürür."""
    try:
        usage = shutil.disk_usage(path)
        # Dosya sistemi tipini al
        fstype = "bilinmiyor"
        try:
            import subprocess
            result = subprocess.run(
                ["df", "-T", path],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    fstype = lines[1].split()[1]
        except Exception:
            pass

        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0,
            "fstype": fstype,
        }
    except OSError:
        return {"total": 0, "used": 0, "free": 0, "percent": 0, "fstype": "?"}


def get_home_dir():
    """Kullanıcının home dizinini döndürür."""
    return os.path.expanduser("~")


def get_username():
    """Kullanıcı adını döndürür."""
    return os.environ.get("USER", os.environ.get("LOGNAME", "kullanıcı"))


def get_kernel_version():
    """Çalışan çekirdek sürümünü döndürür."""
    try:
        return os.uname().release
    except Exception:
        return "bilinmiyor"
