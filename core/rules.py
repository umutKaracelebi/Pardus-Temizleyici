"""
Pardus Sistem Temizleyici — Kural Motoru

mcdu (https://github.com/mikalv/mcdu) ilhamıyla:
Kurallar dosya tabanlı tanımlanır, motor bunları tarar.

Her kural:
  - name: benzersiz tanımlayıcı
  - category: UI'da gruplamak için kategori
  - description: açıklama
  - path: taranacak dizin (${HOME} değişkeni desteklenir)
  - match_type: "file", "directory", "both"
  - pattern: glob deseni (opsiyonel)
  - min_age_hours: dosya en az bu kadar eski olmalı (opsiyonel)
  - min_size_bytes: minimum boyut (opsiyonel)
  - project_marker: üst dizinde olması gereken dosya (opsiyonel)
  - max_depth: recursive derinlik limiti (opsiyonel)
  - enabled: False ise atlanır (varsayılan True)
  - risky: True ise UI'da uyarı gösterilir
  - warning: uyarı mesajı
"""

import os
import time
import fnmatch
from pathlib import Path

from utils.system_info import get_home_dir


def _expand_path(path_str):
    """${HOME} gibi değişkenleri çözer."""
    home = get_home_dir()
    return path_str.replace("${HOME}", home)


# ══════════════════════════════════════════════════════════════
# LINUX CLEANUP KURALLARI (mcdu defaults.toml'dan portlanmıştır)
# ══════════════════════════════════════════════════════════════

CLEANUP_RULES = [
    # ─── Sistem Temizliği ─────────────────────────────────────
    {
        "name": "apt-cache",
        "category": "Sistem",
        "description": "APT indirme önbelleği (.deb dosyaları)",
        "path": "/var/cache/apt/archives",
        "pattern": "*.deb",
        "match_type": "file",
    },
    {
        "name": "journal-logs",
        "category": "Sistem",
        "description": "7 günden eski sistem logları",
        "path": "/var/log/journal",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "old-logs",
        "category": "Sistem",
        "description": "Rotasyonlu eski log dosyaları",
        "path": "/var/log",
        "pattern": "*.gz",
        "match_type": "file",
    },
    {
        "name": "old-logs-numbered",
        "category": "Sistem",
        "description": "Numaralı eski log dosyaları",
        "path": "/var/log",
        "pattern": "*.1",
        "match_type": "file",
    },
    {
        "name": "trash",
        "category": "Sistem",
        "description": "Çöp kutusundaki dosyalar",
        "path": "${HOME}/.local/share/Trash",
        "match_type": "both",
        "risky": True,
        "warning": "Çöp kutusundaki öğeler kalıcı olarak silinecek",
    },

    # ─── Kullanıcı Önbelleği ─────────────────────────────────
    {
        "name": "thumbnails",
        "category": "Kullanıcı Önbelleği",
        "description": "Dosya yöneticisi küçük resimleri",
        "path": "${HOME}/.cache/thumbnails",
        "match_type": "both",
    },
    {
        "name": "gnome-thumbnailer",
        "category": "Kullanıcı Önbelleği",
        "description": "GNOME küçük resim oluşturucu cache",
        "path": "${HOME}/.cache/gnome-desktop-thumbnailer",
        "match_type": "both",
    },
    {
        "name": "clipboard-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "Pano geçmişi önbelleği",
        "path": "${HOME}/.cache/clipboard-indicator@tudmotu.com",
        "match_type": "both",
    },
    {
        "name": "gnome-software-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "GNOME Yazılım Mağazası önbelleği",
        "path": "${HOME}/.cache/gnome-software",
        "match_type": "both",
    },
    {
        "name": "gnome-shell-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "GNOME Shell uzantı önbelleği",
        "path": "${HOME}/.cache/gnome-shell",
        "match_type": "both",
    },
    {
        "name": "flatpak-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "Flatpak uygulama önbelleği",
        "path": "${HOME}/.cache/flatpak",
        "match_type": "both",
    },
    {
        "name": "crash-reports",
        "category": "Kullanıcı Önbelleği",
        "description": "Eski çökme raporları",
        "path": "${HOME}/.cache/crash",
        "match_type": "both",
    },
    {
        "name": "appstream-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "AppStream metadata önbelleği",
        "path": "${HOME}/.cache/appstream",
        "match_type": "both",
    },
    {
        "name": "shumate-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "Harita döşeme önbelleği",
        "path": "${HOME}/.cache/shumate",
        "match_type": "both",
    },
    {
        "name": "vlc-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "VLC medya oynatıcı önbelleği",
        "path": "${HOME}/.cache/vlc",
        "match_type": "both",
    },
    {
        "name": "zoom-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "Zoom toplantı önbelleği",
        "path": "${HOME}/.cache/zoom",
        "match_type": "both",
    },
    {
        "name": "pardus-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "Pardus uygulama önbelleği",
        "path": "${HOME}/.cache/pardus",
        "match_type": "both",
    },
    {
        "name": "event-sound-cache",
        "category": "Kullanıcı Önbelleği",
        "description": "Sistem sesi önbelleği",
        "path": "${HOME}/.cache",
        "pattern": "event-sound-cache*",
        "match_type": "file",
    },
    {
        "name": "recently-used",
        "category": "Kullanıcı Önbelleği",
        "description": "Son kullanılan dosyalar listesi",
        "path": "${HOME}/.local/share",
        "pattern": "recently-used.xbel",
        "match_type": "file",
    },

    # ─── Geliştirici Artıkları — Sabit Cache'ler ─────────────
    {
        "name": "npm-cache",
        "category": "Geliştirici (Cache)",
        "description": "npm paket önbelleği",
        "path": "${HOME}/.npm/_cacache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "yarn-cache",
        "category": "Geliştirici (Cache)",
        "description": "Yarn paket önbelleği",
        "path": "${HOME}/.cache/yarn",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "pnpm-store",
        "category": "Geliştirici (Cache)",
        "description": "pnpm paket deposu",
        "path": "${HOME}/.local/share/pnpm/store",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "bun-cache",
        "category": "Geliştirici (Cache)",
        "description": "Bun paket önbelleği",
        "path": "${HOME}/.bun/install/cache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "cargo-registry-cache",
        "category": "Geliştirici (Cache)",
        "description": "Rust crate indirme önbelleği",
        "path": "${HOME}/.cargo/registry/cache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "cargo-registry-src",
        "category": "Geliştirici (Cache)",
        "description": "Rust crate kaynak dosyaları",
        "path": "${HOME}/.cargo/registry/src",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "cargo-git-checkouts",
        "category": "Geliştirici (Cache)",
        "description": "Cargo git bağımlılıkları",
        "path": "${HOME}/.cargo/git/checkouts",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "go-build-cache",
        "category": "Geliştirici (Cache)",
        "description": "Go derleme önbelleği",
        "path": "${HOME}/.cache/go-build",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "go-mod-cache",
        "category": "Geliştirici (Cache)",
        "description": "Go modül önbelleği",
        "path": "${HOME}/go/pkg/mod/cache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "gradle-caches",
        "category": "Geliştirici (Cache)",
        "description": "Gradle bağımlılık önbelleği",
        "path": "${HOME}/.gradle/caches",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "maven-repository",
        "category": "Geliştirici (Cache)",
        "description": "Maven yerel depo",
        "path": "${HOME}/.m2/repository",
        "match_type": "both",
        "min_age_hours": 720,
    },
    {
        "name": "composer-cache",
        "category": "Geliştirici (Cache)",
        "description": "PHP Composer önbelleği",
        "path": "${HOME}/.composer/cache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "gem-cache",
        "category": "Geliştirici (Cache)",
        "description": "Ruby gem önbelleği",
        "path": "${HOME}/.gem",
        "match_type": "both",
        "min_age_hours": 720,
    },
    {
        "name": "pip-cache",
        "category": "Geliştirici (Cache)",
        "description": "pip indirme önbelleği (wheels)",
        "path": "${HOME}/.cache/pip/wheels",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "pip-http-cache",
        "category": "Geliştirici (Cache)",
        "description": "pip HTTP önbelleği",
        "path": "${HOME}/.cache/pip/http-v2",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "conda-pkgs",
        "category": "Geliştirici (Cache)",
        "description": "Conda paket önbelleği",
        "path": "${HOME}/miniconda3/pkgs",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "conda-pkgs-anaconda",
        "category": "Geliştirici (Cache)",
        "description": "Anaconda paket önbelleği",
        "path": "${HOME}/anaconda3/pkgs",
        "match_type": "both",
        "min_age_hours": 168,
    },

    # ─── IDE Önbellekleri ─────────────────────────────────────
    {
        "name": "vscode-cache",
        "category": "IDE Önbellekleri",
        "description": "VS Code önbelleği",
        "path": "${HOME}/.config/Code/Cache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "vscode-cached-data",
        "category": "IDE Önbellekleri",
        "description": "VS Code önbellek verileri",
        "path": "${HOME}/.config/Code/CachedData",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "vscode-cached-extensions",
        "category": "IDE Önbellekleri",
        "description": "VS Code eklenti önbelleği",
        "path": "${HOME}/.config/Code/CachedExtensionVSIXs",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "jetbrains-cache",
        "category": "IDE Önbellekleri",
        "description": "JetBrains IDE önbelleği",
        "path": "${HOME}/.cache/JetBrains",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "jetbrains-logs",
        "category": "IDE Önbellekleri",
        "description": "JetBrains IDE logları",
        "path": "${HOME}/.local/share/JetBrains",
        "pattern": "**/log/**",
        "match_type": "both",
        "min_age_hours": 168,
    },

    # ─── DevOps ─────────────────────────────────────────────
    {
        "name": "kubectl-cache",
        "category": "DevOps",
        "description": "kubectl önbelleği",
        "path": "${HOME}/.kube/cache",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "helm-cache",
        "category": "DevOps",
        "description": "Helm chart önbelleği",
        "path": "${HOME}/.cache/helm",
        "match_type": "both",
        "min_age_hours": 168,
    },
    {
        "name": "terraform-plugin-cache",
        "category": "DevOps",
        "description": "Terraform plugin önbelleği",
        "path": "${HOME}/.terraform.d/plugin-cache",
        "match_type": "both",
        "min_age_hours": 720,
    },
    {
        "name": "docker-build-cache",
        "category": "DevOps",
        "description": "Docker BuildKit önbelleği",
        "path": "${HOME}/.cache/docker",
        "match_type": "both",
        "min_age_hours": 168,
    },
]

# ══════════════════════════════════════════════════════════════
# Proje dizinlerinde aranacak build artıkları
# (dizin_adı, proje_belirteci, açıklama)
# ══════════════════════════════════════════════════════════════
PROJECT_ARTIFACT_RULES = [
    ("node_modules", "package.json", "Node.js bağımlılıkları"),
    ("__pycache__", None, "Python bytecode önbelleği"),
    (".venv", "pyproject.toml", "Python sanal ortam"),
    ("venv", "requirements.txt", "Python sanal ortam"),
    ("target", "Cargo.toml", "Rust derleme çıktıları"),
    (".gradle", None, "Gradle proje önbelleği"),
    (".terraform", None, "Terraform çalışma dizini"),
    (".next", "package.json", "Next.js derleme çıktıları"),
    ("dist", "package.json", "Frontend dağıtım çıktıları"),
    ("build", "build.gradle", "Java/Gradle derleme çıktıları"),
    ("_build", "mix.exs", "Elixir derleme çıktıları"),
    ("deps", "mix.exs", "Elixir bağımlılıkları"),
    ("zig-cache", "build.zig", "Zig derleme önbelleği"),
    ("zig-out", "build.zig", "Zig derleme çıktıları"),
]

# Proje aranacak dizinler
PROJECT_SCAN_DIRS = [
    "Projects", "Code", "repos", "dev", "src",
    "workspace", "Developer", "projects", "Projeler",
]


class RuleEngine:
    """Kural tabanlı tarama motoru."""

    def __init__(self):
        self._home = get_home_dir()

    def scan_rule(self, rule):
        """Tek bir kuralı tarar. (path, size) listesi döndürür."""
        if not rule.get("enabled", True):
            return [], 0

        path = _expand_path(rule["path"])
        if not os.path.exists(path):
            return [], 0

        match_type = rule.get("match_type", "both")
        pattern = rule.get("pattern")
        min_age = rule.get("min_age_hours", 0)
        min_size = rule.get("min_size_bytes", 0)
        cutoff = time.time() - (min_age * 3600) if min_age else 0

        files = []
        total_size = 0

        try:
            if pattern and not pattern.startswith("**"):
                # Sadece path altında pattern'e uyan dosya/dizinleri bul
                for entry in os.scandir(path):
                    if not fnmatch.fnmatch(entry.name, pattern):
                        continue
                    if match_type == "file" and not entry.is_file():
                        continue
                    if match_type == "directory" and not entry.is_dir():
                        continue

                    try:
                        stat = entry.stat(follow_symlinks=False)
                        if cutoff and stat.st_mtime > cutoff:
                            continue
                        if entry.is_dir():
                            size = self._dir_size(entry.path)
                        else:
                            size = stat.st_size
                        if size >= min_size and size > 0:
                            files.append((entry.path, size))
                            total_size += size
                    except (OSError, PermissionError):
                        continue
            else:
                # Tüm path dizininin boyutunu hesapla
                size = self._dir_size(path)
                if size > 0:
                    files.append((path, size))
                    total_size = size

        except (OSError, PermissionError):
            pass

        return files, total_size

    def scan_all_rules(self, category_filter=None):
        """Tüm kuralları (veya belirli kategori) tarar."""
        results = {}
        for rule in CLEANUP_RULES:
            if category_filter and rule["category"] != category_filter:
                continue
            files, total = self.scan_rule(rule)
            if total > 0:
                results[rule["name"]] = {
                    "files": files,
                    "total_size": total,
                    "description": rule["description"],
                    "category": rule["category"],
                    "risky": rule.get("risky", False),
                    "warning": rule.get("warning", ""),
                }
        return results

    def scan_project_artifacts(self, extra_dirs=None):
        """Proje dizinlerindeki build artıklarını tarar."""
        roots = []
        for dirname in PROJECT_SCAN_DIRS:
            candidate = os.path.join(self._home, dirname)
            if os.path.isdir(candidate):
                roots.append(candidate)

        if extra_dirs:
            roots.extend(extra_dirs)

        results = []
        skip = {".git", "node_modules", "target", ".venv", "venv"}

        for root in roots:
            self._find_project_artifacts(root, skip, 5, 0, results)

        return results

    def _find_project_artifacts(self, path, skip, max_depth, depth, results):
        """Recursive proje artığı arama."""
        if depth >= max_depth:
            return

        try:
            for entry in os.scandir(path):
                if not entry.is_dir(follow_symlinks=False):
                    continue

                # Gizli dizinleri kontrol et
                if entry.name.startswith(".") and entry.name not in (
                    ".venv", ".gradle", ".terraform", ".next"
                ):
                    continue

                # Hedef mi kontrol et
                matched = False
                for target_name, marker, desc in PROJECT_ARTIFACT_RULES:
                    if entry.name == target_name:
                        if marker:
                            parent = os.path.dirname(entry.path)
                            if not any(
                                f.endswith(marker.lstrip("*"))
                                for f in os.listdir(parent)
                                if os.path.isfile(os.path.join(parent, f))
                            ):
                                continue
                        size = self._dir_size(entry.path)
                        if size > 1024 * 1024:  # 1 MB minimum
                            results.append((entry.path, size, desc))
                        matched = True
                        break

                if not matched and entry.name not in skip:
                    self._find_project_artifacts(
                        entry.path, skip, max_depth, depth + 1, results
                    )
        except (OSError, PermissionError):
            pass

    def _dir_size(self, path, max_files=5000):
        """Dizin boyutunu hesaplar."""
        total = 0
        count = 0
        try:
            for root, dirs, filenames in os.walk(path):
                for f in filenames:
                    if count >= max_files:
                        return total
                    try:
                        total += os.lstat(os.path.join(root, f)).st_size
                        count += 1
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        return total
