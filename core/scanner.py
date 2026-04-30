"""
Pardus Sistem Temizleyici — Tarama motoru

Kural tabanlı tarama: core/rules.py'deki CLEANUP_RULES kullanılır.
mcdu (https://github.com/mikalv/mcdu) yaklaşımından esinlenilmiştir.
"""

import os
import subprocess
import threading

from utils.system_info import get_home_dir, get_kernel_version
from core.rules import RuleEngine, CLEANUP_RULES, _expand_path


class ScanResult:
    """Tek bir kategori için tarama sonucu."""

    def __init__(self, category_id, files=None, total_size=0, details=""):
        self.category_id = category_id
        self.files = files or []
        self.total_size = total_size
        self.details = details
        self.selected = True
        # Dosya bazlı seçim: her dosya varsayılan seçili
        self.file_selected = [True] * len(self.files)

    def get_selected_files(self):
        """Sadece seçili dosyaları döndür."""
        return [
            (path, size)
            for (path, size), sel in zip(self.files, self.file_selected)
            if sel
        ]

    @property
    def selected_size(self):
        """Seçili dosyaların toplam boyutu."""
        if not self.files:
            return self.total_size if self.selected else 0
        return sum(
            size for (_, size), sel in zip(self.files, self.file_selected) if sel
        )


class Scanner:
    """Kural tabanlı sistem tarama motoru."""

    def __init__(self):
        self._cancel = False
        self._lock = threading.Lock()
        self.results = {}
        self._engine = RuleEngine()

    def cancel(self):
        with self._lock:
            self._cancel = True

    def is_cancelled(self):
        with self._lock:
            return self._cancel

    def scan_all(self, progress_callback=None, done_callback=None):
        """Tüm kategorileri tarar."""
        self._cancel = False
        self.results = {}

        # Kategori tarama fonksiyonları
        categories = [
            ("apt_cache", "APT Önbelleği", self._scan_apt_cache),
            ("apt_autoremove", "Gereksiz Paketler", self._scan_apt_autoremove),
            ("old_kernels", "Eski Çekirdekler", self._scan_old_kernels),
            ("user_cache", "Kullanıcı Önbelleği", self._scan_user_cache),
            ("thumbnails", "Küçük Resimler", self._scan_thumbnails),
            ("journal_logs", "Sistem Logları", self._scan_journal_logs),
            ("trash", "Çöp Kutusu", self._scan_trash),
            ("temp_files", "Geçici Dosyalar", self._scan_temp_files),
            ("dev_artifacts", "Geliştirici Artıkları", self._scan_dev_artifacts),
            ("duplicates", "Yinelenen Dosyalar", self._scan_duplicates),
        ]

        total = len(categories)
        for i, (cat_id, name, scan_func) in enumerate(categories):
            if self.is_cancelled():
                break

            try:
                result = scan_func()
                self.results[cat_id] = result
            except Exception as e:
                self.results[cat_id] = ScanResult(
                    cat_id, details=f"Tarama hatası: {e}"
                )

            if progress_callback:
                progress_callback(cat_id, i + 1, total)

        if done_callback:
            done_callback(self.results)

        return self.results

    # ═══════════════════════════════════════════════════════════
    # KATEGORİ TARAMA FONKSİYONLARI
    # ═══════════════════════════════════════════════════════════

    def _scan_apt_cache(self):
        """APT önbellek dosyalarını tarar — apt-get clean'in yapacağı iş."""
        rule = {"path": "/var/cache/apt/archives", "pattern": "*.deb", "match_type": "file"}
        files, total = self._engine.scan_rule(rule)
        return ScanResult("apt_cache", files, total, f"{len(files)} {_('adet .deb dosyası')}")

    def _scan_apt_autoremove(self):
        """Artık gerekmeyen paketleri tarar — apt autoremove."""
        import re
        packages = []
        total_size = 0

        try:
            result = subprocess.run(
                ["apt-get", "--dry-run", "autoremove"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.startswith("Remv "):
                        parts = line.split()
                        if len(parts) >= 2:
                            packages.append((parts[1], 0))

                for line in result.stdout.split("\n"):
                    if "disk alanı" in line.lower() or "disk space" in line.lower() or "freed" in line.lower():
                        numbers = re.findall(r'[\d,.]+', line)
                        if numbers:
                            try:
                                size_str = numbers[0].replace(",", ".")
                                size = float(size_str)
                                if "GB" in line or "gb" in line:
                                    total_size = int(size * 1024**3)
                                elif "MB" in line or "mb" in line or "mB" in line:
                                    total_size = int(size * 1024**2)
                                elif "kB" in line or "KB" in line:
                                    total_size = int(size * 1024)
                                else:
                                    total_size = int(size)
                            except ValueError:
                                pass
        except Exception:
            pass

        return ScanResult("apt_autoremove", packages, total_size, f"{len(packages)} {_('gereksiz paket')}")

    def _scan_old_kernels(self):
        """Eski çekirdek dosyalarını tarar."""
        current_kernel = get_kernel_version()
        old_kernels = []
        total_size = 0

        try:
            result = subprocess.run(
                ["dpkg", "-l", "linux-image-*"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("ii") and "linux-image-" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            pkg_name = parts[1]
                            if current_kernel in pkg_name:
                                continue
                            if pkg_name in ("linux-image-amd64", "linux-image-generic"):
                                continue

                            try:
                                size_result = subprocess.run(
                                    ["dpkg-query", "-W", "-f=${Installed-Size}", pkg_name],
                                    capture_output=True, text=True, timeout=5
                                )
                                size = int(size_result.stdout.strip()) * 1024 if size_result.returncode == 0 else 0
                            except Exception:
                                size = 0

                            old_kernels.append((pkg_name, size))
                            total_size += size
        except Exception:
            pass

        return ScanResult("old_kernels", old_kernels, total_size, f"{len(old_kernels)} {_('eski çekirdek')}")

    def _scan_user_cache(self):
        """Kullanıcı önbelleğini kural motoruyla tarar."""
        user_cache_rules = [r for r in CLEANUP_RULES if r["category"] == "Kullanıcı Önbelleği"]
        files = []
        total_size = 0

        for rule in user_cache_rules:
            if self.is_cancelled():
                break
            rule_files, rule_total = self._engine.scan_rule(rule)
            files.extend(rule_files)
            total_size += rule_total

        return ScanResult("user_cache", files, total_size, f"{len(files)} {_('önbellek öğesi')}")

    def _scan_thumbnails(self):
        """Küçük resim dosyalarını tarar."""
        rule = {"path": _expand_path("${HOME}/.cache/thumbnails"), "match_type": "both"}
        files, total = self._engine.scan_rule(rule)
        return ScanResult("thumbnails", files, total, f"{len(files)} {_('küçük resim')}")

    def _scan_journal_logs(self):
        """Sistem journal loglarını tarar."""
        import re
        total_size = 0
        details = ""

        try:
            result = subprocess.run(
                ["journalctl", "--disk-usage"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                numbers = re.findall(r'([\d.]+)\s*([KMGT])', output)
                if numbers:
                    size_val = float(numbers[0][0])
                    unit = numbers[0][1]
                    multiplier = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
                    total_size = int(size_val * multiplier.get(unit, 1))
                    total_size = int(total_size * 0.6)
                    details = f"{_('Tahmini eski log:')} {output}"
        except Exception:
            pass

        return ScanResult("journal_logs", [], total_size, details)

    def _scan_trash(self):
        """Çöp kutusundaki dosyaları tarar."""
        home = get_home_dir()
        trash_dirs = [
            os.path.join(home, ".local", "share", "Trash", "files"),
            os.path.join(home, ".local", "share", "Trash", "info"),
        ]

        files = []
        total_size = 0

        for trash_dir in trash_dirs:
            if os.path.isdir(trash_dir):
                dir_size = self._engine._dir_size(trash_dir)
                if dir_size > 0:
                    files.append((trash_dir, dir_size))
                    total_size += dir_size

        return ScanResult("trash", files, total_size, f"{len(files)} {_('çöp dizini/dosyası')}")

    def _scan_temp_files(self):
        """/tmp altındaki eski geçici dosyaları tarar."""
        import time
        files = []
        total_size = 0
        cutoff = time.time() - (7 * 24 * 3600)

        try:
            for entry in os.scandir("/tmp"):
                try:
                    stat = entry.stat(follow_symlinks=False)
                    if stat.st_mtime < cutoff:
                        if entry.is_file(follow_symlinks=False):
                            files.append((entry.path, stat.st_size))
                            total_size += stat.st_size
                        elif entry.is_dir(follow_symlinks=False):
                            dir_size = self._engine._dir_size(entry.path)
                            if dir_size > 0:
                                files.append((entry.path, dir_size))
                                total_size += dir_size
                except (OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            pass

        return ScanResult("temp_files", files, total_size, f"{len(files)} {_('eski geçici dosya')}")

    def _scan_dev_artifacts(self):
        """Geliştirici artıklarını kural motoruyla tarar."""
        # 1. Sabit cache kuralları
        dev_cache_rules = [r for r in CLEANUP_RULES if r["category"] in (
            "Geliştirici (Cache)", "IDE Önbellekleri", "DevOps"
        )]

        files = []
        total_size = 0

        for rule in dev_cache_rules:
            if self.is_cancelled():
                break
            rule_files, rule_total = self._engine.scan_rule(rule)
            files.extend(rule_files)
            total_size += rule_total

        # 2. Proje dizinlerindeki build artıkları
        if not self.is_cancelled():
            project_results = self._engine.scan_project_artifacts()
            for path, size, desc in project_results:
                files.append((path, size))
                total_size += size

        return ScanResult("dev_artifacts", files, total_size, f"{len(files)} {_('geliştirici artığı')}")

    def _scan_duplicates(self):
        """Yinelenen dosyaları tarar — boyut + hash, grup bilgisiyle."""
        import hashlib
        home = get_home_dir()
        min_size = 10 * 1024  # 10KB altı dosyaları atla (eskiden 100KB idi, küçük .odt vb. için düşürdük)
        max_depth = 6

        # Adım 1: Boyuta göre grupla
        size_map = {}  # size -> [path, ...]

        # Sadece kullanıcı dosyalarına odaklan (sistem/uygulama dosyalarını atla)
        allowed_exts = {
            # Belgeler
            '.pdf', '.doc', '.docx', '.odt', '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp', '.txt', '.rtf', '.csv',
            # Resimler
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff',
            # Videolar
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            # Sesler
            '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac',
            # Arşivler / İmajlar
            '.zip', '.rar', '.7z', '.tar', '.gz', '.iso'
        }

        def walk_dir(path, depth=0):
            if depth > max_depth or self.is_cancelled():
                return
            try:
                for entry in os.scandir(path):
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file():
                            st = entry.stat()
                            if st.st_size >= min_size:
                                ext = os.path.splitext(entry.name)[1].lower()
                                if ext in allowed_exts:
                                    size_map.setdefault(st.st_size, []).append(entry.path)
                        elif entry.is_dir():
                            # Sadece izin verilen standart klasörler içinde derine in
                            # .cache vb. gizli klasörler zaten taranmayacak
                            if not entry.name.startswith('.'):
                                walk_dir(entry.path, depth + 1)
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError):
                pass

        # Tüm ev dizinini rastgele taramak yerine sadece güvenli kullanıcı klasörlerini tara
        from gi.repository import GLib
        xdg_dirs = [
            GLib.UserDirectory.DIRECTORY_DESKTOP,
            GLib.UserDirectory.DIRECTORY_DOCUMENTS,
            GLib.UserDirectory.DIRECTORY_DOWNLOAD,
            GLib.UserDirectory.DIRECTORY_MUSIC,
            GLib.UserDirectory.DIRECTORY_PICTURES,
            GLib.UserDirectory.DIRECTORY_VIDEOS,
        ]
        
        for dir_type in xdg_dirs:
            path = GLib.get_user_special_dir(dir_type)
            if path and os.path.exists(path) and path.startswith(home):
                walk_dir(path)

        # Adım 2: Aynı boyuttaki dosyaları hash'le — GRUPLAR oluştur
        # groups: [ { "name": "dosya.pdf", "size": 1234, "paths": [path1, path2, ...] }, ... ]
        groups = []
        duplicates = []  # flat: (path, size) — varsayılan silinecekler
        total_size = 0

        for fsize, paths in size_map.items():
            if len(paths) < 2 or self.is_cancelled():
                continue

            hash_groups = {}  # hash -> [path, ...]
            for path in paths:
                try:
                    h = hashlib.md5()
                    with open(path, 'rb') as f:
                        h.update(f.read(8192))
                        f.seek(max(0, fsize - 8192))
                        h.update(f.read(8192))
                    digest = h.hexdigest()
                    hash_groups.setdefault(digest, []).append(path)
                except (OSError, PermissionError):
                    continue

            for digest, group_paths in hash_groups.items():
                if len(group_paths) < 2:
                    continue

                name = os.path.basename(group_paths[0])
                groups.append({
                    "name": name,
                    "size": fsize,
                    "paths": group_paths,  # Tümü
                })

                # Flat listeye ekle: HEPSİNİ ekle
                for p in group_paths:
                    duplicates.append((p, fsize))
                    # total_size hesabına hepsi dahil olmasın diye aşağıda hallediyoruz
                    # aslında hepsi potansiyel silinebilir, o yüzden hepsini ekleyelim
                    total_size += fsize

        result = ScanResult(
            "duplicates", duplicates, total_size,
            f"{len(groups)} {_('yinelenen dosya grubu')}"
        )
        # Grup bilgisini ekstra olarak sakla
        result.duplicate_groups = groups

        # İlk dosyaları varsayılan olarak korunacak (seçimsiz) yap
        file_idx = 0
        for g in groups:
            result.file_selected[file_idx] = False  # İlkini koru
            file_idx += len(g["paths"])

        return result

    def estimate_category_size(self, cat_id, engine=None):
        """Hızlı kategori boyutu tahmini (home view için)."""
        eng = engine or self._engine

        estimators = {
            "apt_cache": lambda: eng.scan_rule({
                "path": "/var/cache/apt/archives", "pattern": "*.deb", "match_type": "file"
            })[1],
            "apt_autoremove": lambda: self._scan_apt_autoremove().total_size,
            "old_kernels": lambda: self._scan_old_kernels().total_size,
            "user_cache": lambda: sum(
                eng.scan_rule(r)[1]
                for r in CLEANUP_RULES if r["category"] == "Kullanıcı Önbelleği"
            ),
            "thumbnails": lambda: eng.scan_rule({
                "path": _expand_path("${HOME}/.cache/thumbnails"), "match_type": "both"
            })[1],
            "journal_logs": lambda: self._scan_journal_logs().total_size,
            "trash": lambda: self._scan_trash().total_size,
            "temp_files": lambda: self._scan_temp_files().total_size,
            "dev_artifacts": lambda: sum(
                eng.scan_rule(r)[1]
                for r in CLEANUP_RULES
                if r["category"] in ("Geliştirici (Cache)", "IDE Önbellekleri", "DevOps")
            ),
            "duplicates": lambda: self._scan_duplicates().total_size,
        }

        fn = estimators.get(cat_id)
        if fn:
            try:
                return fn()
            except Exception:
                return 0
        return 0
