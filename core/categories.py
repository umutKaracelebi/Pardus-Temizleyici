"""
Pardus Sistem Temizleyici — Kategori tanımları
"""

CATEGORIES = [
    {
        "id": "apt_cache",
        "name": _("APT Önbelleği"),
        "description": _("İndirilen .deb paket dosyaları"),
        "icon": "package-x-generic-symbolic",
        "risk": "low",
        "requires_root": True,
        "color": "#4A90D9",
    },
    {
        "id": "apt_autoremove",
        "name": _("Gereksiz Paketler"),
        "description": _("Artık gerekmeyen bağımlılıklar"),
        "icon": "edit-delete-symbolic",
        "risk": "medium",
        "requires_root": True,
        "color": "#E67E22",
    },
    {
        "id": "old_kernels",
        "name": _("Eski Çekirdekler"),
        "description": _("Kullanılmayan eski kernel dosyaları"),
        "icon": "application-x-firmware-symbolic",
        "risk": "medium",
        "requires_root": True,
        "color": "#9B59B6",
    },
    {
        "id": "user_cache",
        "name": _("Kullanıcı Önbelleği"),
        "description": _("Uygulama önbellek dosyaları (~/.cache)"),
        "icon": "folder-templates-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#2ECC71",
    },
    {
        "id": "thumbnails",
        "name": _("Küçük Resimler"),
        "description": _("Dosya yöneticisi küçük resimleri"),
        "icon": "image-x-generic-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#1ABC9C",
    },
    {
        "id": "journal_logs",
        "name": _("Sistem Günlükleri"),
        "description": _("Sistem hata ve olay kayıtları"),
        "icon": "format-text-direction-ltr-symbolic",
        "risk": "low",
        "requires_root": True,
        "color": "#F1C40F",
    },
    {
        "id": "trash",
        "name": _("Çöp Kutusu"),
        "description": _("Silinmiş dosyalar"),
        "icon": "user-trash-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#E74C3C",
    },
    {
        "id": "temp_files",
        "name": _("Geçici Dosyalar"),
        "description": _("/tmp altındaki kullanıcınıza ait dosyalar"),
        "icon": "document-open-recent-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#95A5A6",
    },
    {
        "id": "dev_artifacts",
        "name": _("Geliştirici Artıkları"),
        "description": _("Projelerdeki gereksiz derleme dosyaları (node_modules, __pycache__, vb.)"),
        "icon": "utilities-terminal-symbolic",
        "risk": "medium",
        "requires_root": False,
        "color": "#34495E",
    },
    {
        "id": "duplicates",
        "name": _("Yinelenen Dosyalar"),
        "description": _("Aynı içeriğe sahip kopyalar (Masaüstü, Belgeler vb.)"),
        "icon": "edit-copy-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#D35400",
    }
]

# Grup tanımları (UI görünümü için sırayı belirler)
GROUPS = [
    {
        "id": "system",
        "name": _("Sistem Kategorileri"),
        "categories": ["apt_cache", "apt_autoremove", "old_kernels", "journal_logs"]
    },
    {
        "id": "user",
        "name": _("Kullanıcı Kategorileri"),
        "categories": ["user_cache", "thumbnails", "trash", "temp_files", "dev_artifacts", "duplicates"]
    }
]

def get_category(cat_id):
    for c in CATEGORIES:
        if c["id"] == cat_id:
            return c
    return None
