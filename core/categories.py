"""
Pardus Sistem Temizleyici — Kategori tanımları

Her kategori:
  - id: benzersiz kimlik
  - name: görüntülenen ad
  - description: açıklama
  - icon: ikon adı (GTK symbolic)
  - risk: "low", "medium", "high"
  - requires_root: root yetki gerekiyor mu
"""

CATEGORIES = [
    {
        "id": "apt_cache",
        "name": "APT Önbelleği",
        "description": "İndirilen .deb paket dosyaları",
        "icon": "package-x-generic-symbolic",
        "risk": "low",
        "requires_root": True,
        "color": "#4A90D9",
    },
    {
        "id": "apt_autoremove",
        "name": "Gereksiz Paketler",
        "description": "Artık gerekmeyen bağımlılıklar",
        "icon": "edit-delete-symbolic",
        "risk": "medium",
        "requires_root": True,
        "color": "#E67E22",
    },
    {
        "id": "old_kernels",
        "name": "Eski Çekirdekler",
        "description": "Kullanılmayan eski kernel dosyaları",
        "icon": "application-x-firmware-symbolic",
        "risk": "medium",
        "requires_root": True,
        "color": "#9B59B6",
    },
    {
        "id": "user_cache",
        "name": "Kullanıcı Önbelleği",
        "description": "Uygulama önbellek dosyaları (~/.cache)",
        "icon": "folder-templates-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#2ECC71",
    },
    {
        "id": "thumbnails",
        "name": "Küçük Resimler",
        "description": "Dosya yöneticisi küçük resimleri",
        "icon": "image-x-generic-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#1ABC9C",
    },
    {
        "id": "journal_logs",
        "name": "Sistem Logları",
        "description": "Eski sistem günlük kayıtları",
        "icon": "text-x-log-symbolic",
        "risk": "low",
        "requires_root": True,
        "color": "#3498DB",
    },
    {
        "id": "trash",
        "name": "Çöp Kutusu",
        "description": "Silinen dosyalar",
        "icon": "user-trash-full-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#E74C3C",
    },
    {
        "id": "temp_files",
        "name": "Geçici Dosyalar",
        "description": "/tmp altındaki eski geçici dosyalar",
        "icon": "document-open-recent-symbolic",
        "risk": "low",
        "requires_root": False,
        "color": "#F39C12",
    },
    {
        "id": "dev_artifacts",
        "name": "Geliştirici Artıkları",
        "description": "Build artıkları, node_modules, __pycache__",
        "icon": "utilities-terminal-symbolic",
        "risk": "medium",
        "requires_root": False,
        "color": "#8E44AD",
    },
    {
        "id": "duplicates",
        "name": "Yinelenen Dosyalar",
        "description": "Birbirinin aynısı olan dosyalar",
        "icon": "edit-copy-symbolic",
        "risk": "medium",
        "requires_root": False,
        "color": "#E91E63",
    },
]


def get_category(category_id):
    """ID'ye göre kategori döndürür."""
    for cat in CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None


def get_safe_categories():
    """Root gerektirmeyen kategorileri döndürür."""
    return [c for c in CATEGORIES if not c["requires_root"]]


def get_root_categories():
    """Root gerektiren kategorileri döndürür."""
    return [c for c in CATEGORIES if c["requires_root"]]
