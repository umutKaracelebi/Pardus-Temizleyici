"""
Pardus Sistem Temizleyici — Temizleme motoru

Her kategori için güvenli temizleme fonksiyonları.
Çift katmanlı güvenlik: dosya yolları her zaman doğrulanır.
Root işlemleri: önce izin alınır, sonra temizleme başlar.
"""

import os
import shutil
import subprocess
import threading
import tempfile

from utils.system_info import get_home_dir


APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELPER_PATH = "/usr/local/bin/pardus-temizleyici-root"
POLICY_PATH = "/usr/share/polkit-1/actions/org.pardus.temizleyici.policy"


class CleanResult:
    """Tek bir kategori için temizleme sonucu."""

    def __init__(self, category_id, success=True, freed_size=0, error=""):
        self.category_id = category_id
        self.success = success
        self.freed_size = freed_size
        self.error = error


class Cleaner:
    """Güvenli temizleme motoru."""

    def __init__(self):
        self._cancel = False
        self._lock = threading.Lock()

    def cancel(self):
        with self._lock:
            self._cancel = True

    def is_cancelled(self):
        with self._lock:
            return self._cancel

    def clean_selected(self, scan_results, progress_callback=None, done_callback=None):
        """Seçili kategorileri temizler."""
        self._cancel = False
        clean_results = {}

        user_categories = []
        root_categories = {}

        for cat_id, scan_result in scan_results.items():
            if not scan_result.selected or scan_result.total_size <= 0:
                continue
            if cat_id in ("apt_cache", "apt_autoremove", "old_kernels", "journal_logs"):
                root_categories[cat_id] = scan_result
            else:
                user_categories.append((cat_id, scan_result))

        total = len(user_categories) + len(root_categories)
        i = 0

        # ═══ ADIM 1: Root kategorileri ═══
        if root_categories and not self.is_cancelled():
            root_result = self._clean_root_categories(root_categories)

            # pkexec iptal edildi mi? (sadece kod 126/127)
            pkexec_dismissed = any(
                not r.success and "iptal" in r.error.lower()
                for r in root_result.values()
            )

            for cat_id, result in root_result.items():
                clean_results[cat_id] = result
                i += 1
                if progress_callback:
                    progress_callback(cat_id, i, total)

            # pkexec iptal edildiyse sadece root kategorileri başarısız,
            # ama kullanıcı kategorileri yine de temizlenir
            if pkexec_dismissed:
                pass  # Devam et, user kategorileri temizlensin

        # ═══ ADIM 2: Kullanıcı kategorileri (root gerektirmez) ═══
        for cat_id, scan_result in user_categories:
            if self.is_cancelled():
                break
            clean_results[cat_id] = self._clean_category(cat_id, scan_result)
            i += 1
            if progress_callback:
                progress_callback(cat_id, i, total)

        if done_callback:
            done_callback(clean_results)

        return clean_results

    def _clean_category(self, cat_id, scan_result):
        """Tek bir kullanıcı kategorisini temizler."""
        cleaners = {
            "user_cache": self._clean_files_in_home,
            "thumbnails": self._clean_files_in_home,
            "trash": self._clean_trash,
            "temp_files": self._clean_temp_files,
            "dev_artifacts": self._clean_files_in_home,
            "duplicates": self._clean_files_in_home,
        }

        cleaner = cleaners.get(cat_id)
        if cleaner:
            return cleaner(cat_id, scan_result)

        return CleanResult(cat_id, False, 0, "Bilinmeyen kategori")

    # ═══════════════════════════════════════════════════════════
    # TEMİZLEME FONKSİYONLARI
    # ═══════════════════════════════════════════════════════════

    def _clean_files_in_home(self, cat_id, scan_result):
        """Ev dizini altındaki dosyaları güvenli siler — sadece seçili dosyalar."""
        freed = 0
        home = get_home_dir()
        selected_files = scan_result.get_selected_files()

        for filepath, size in selected_files:
            if self.is_cancelled():
                break
            try:
                if not filepath.startswith(home):
                    continue
                if os.path.isdir(filepath):
                    shutil.rmtree(filepath, ignore_errors=True)
                else:
                    os.remove(filepath)
                freed += size
            except (OSError, PermissionError):
                continue

        return CleanResult(cat_id, True, freed)

    def _clean_trash(self, cat_id, scan_result):
        """Çöp kutusunu temizler."""
        freed = 0
        home = get_home_dir()
        trash_base = os.path.join(home, ".local", "share", "Trash")

        for subdir in ("files", "info"):
            trash_dir = os.path.join(trash_base, subdir)
            if os.path.isdir(trash_dir):
                for entry in os.scandir(trash_dir):
                    if self.is_cancelled():
                        break
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            size = sum(
                                f.stat().st_size
                                for f in __import__("pathlib").Path(entry.path).rglob("*")
                                if f.is_file()
                            )
                            shutil.rmtree(entry.path, ignore_errors=True)
                        else:
                            size = entry.stat().st_size
                            os.remove(entry.path)
                        freed += size
                    except (OSError, PermissionError):
                        continue

        return CleanResult(cat_id, True, freed)

    def _clean_temp_files(self, cat_id, scan_result):
        """Eski geçici dosyaları temizler — sadece seçili dosyalar."""
        freed = 0
        selected_files = scan_result.get_selected_files()

        for filepath, size in selected_files:
            if self.is_cancelled():
                break
            try:
                if not filepath.startswith("/tmp"):
                    continue
                if os.path.isdir(filepath):
                    shutil.rmtree(filepath, ignore_errors=True)
                else:
                    os.remove(filepath)
                freed += size
            except (OSError, PermissionError):
                continue

        return CleanResult("temp_files", True, freed)

    def _clean_root_categories(self, categories):
        """Root gerektiren kategorileri pkexec ile temizler."""
        results = {}

        commands = []
        for cat_id in categories:
            if cat_id == "apt_cache":
                commands.append("apt-get clean")
            elif cat_id == "apt_autoremove":
                commands.append("apt-get -y autoremove")
            elif cat_id == "old_kernels":
                scan_result = categories[cat_id]
                pkgs = [pkg for pkg, _ in scan_result.files if pkg]
                if pkgs:
                    commands.append(f"apt-get -y purge {' '.join(pkgs)}")
            elif cat_id == "journal_logs":
                commands.append("journalctl --vacuum-time=7d")

        if not commands:
            for cat_id in categories:
                results[cat_id] = CleanResult(cat_id, True, 0)
            return results

        try:
            result = self._run_as_root(commands)

            # pkexec iptal durumu
            if result.returncode in (126, 127):
                for cat_id in categories:
                    results[cat_id] = CleanResult(
                        cat_id, False, 0, "Yönetici izni iptal edildi"
                    )
                return results

            success = result.returncode == 0

            for cat_id, scan_result in categories.items():
                results[cat_id] = CleanResult(
                    cat_id,
                    success=success,
                    freed_size=scan_result.total_size if success else 0,
                    error="" if success else result.stderr[:200]
                )

        except subprocess.TimeoutExpired:
            for cat_id in categories:
                results[cat_id] = CleanResult(cat_id, False, 0, "Zaman aşımı")
        except FileNotFoundError:
            for cat_id in categories:
                results[cat_id] = CleanResult(cat_id, False, 0, "pkexec bulunamadı")
        except Exception as e:
            for cat_id in categories:
                results[cat_id] = CleanResult(cat_id, False, 0, str(e))

        return results

    def _run_as_root(self, commands):
        """Komutları root olarak çalıştır — helper varsa güzel mesajla, yoksa kurup çalıştır."""

        if os.path.exists(HELPER_PATH) and os.path.exists(POLICY_PATH):
            # Helper kurulu — güzel mesajla çalıştır
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".cmds", delete=False, prefix="pardus-clean-"
            ) as tmp:
                for cmd in commands:
                    tmp.write(cmd + "\n")
                cmds_path = tmp.name
            os.chmod(cmds_path, 0o644)

            return subprocess.run(
                ["pkexec", HELPER_PATH, cmds_path],
                capture_output=True, text=True, timeout=300
            )

        # Helper kurulu değil — hem kur hem temizle tek seferde
        helper_src = os.path.join(APP_DIR, "data", "pardus-temizleyici-root")
        policy_src = os.path.join(APP_DIR, "data", "org.pardus.temizleyici.policy")

        install_cmds = []
        if os.path.exists(helper_src):
            install_cmds.append(f"cp '{helper_src}' '{HELPER_PATH}'")
            install_cmds.append(f"chmod 755 '{HELPER_PATH}'")
        if os.path.exists(policy_src):
            install_cmds.append(f"cp '{policy_src}' '{POLICY_PATH}'")

        all_cmds = install_cmds + commands
        full_cmd = " && ".join(all_cmds)

        return subprocess.run(
            ["pkexec", "bash", "-c", full_cmd],
            capture_output=True, text=True, timeout=300
        )
