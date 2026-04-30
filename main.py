#!/usr/bin/env python3
"""
Pardus Sistem Temizleyici — Giriş Noktası

Modern, güvenli ve kullanıcı dostu Linux sistem temizleme aracı.
"""

import sys
import os
import gettext
import locale

# Modül yolunu ayarla
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# Çeviri Altyapısı (i18n)
TRANSLATIONS_EN = {
    "APT Önbelleği": "APT Cache",
    "İndirilen .deb paket dosyaları": "Downloaded .deb package files",
    "Gereksiz Paketler": "Unnecessary Packages",
    "Artık gerekmeyen bağımlılıklar": "Dependencies no longer needed",
    "Eski Çekirdekler": "Old Kernels",
    "Kullanılmayan eski kernel dosyaları": "Unused old kernel files",
    "Kullanıcı Önbelleği": "User Cache",
    "Uygulama önbellek dosyaları (~/.cache)": "Application cache files (~/.cache)",
    "Küçük Resimler": "Thumbnails",
    "Dosya yöneticisi küçük resimleri": "File manager thumbnails",
    "Sistem Günlükleri": "System Logs",
    "Sistem hata ve olay kayıtları": "System error and event logs",
    "Çöp Kutusu": "Trash",
    "Silinmiş dosyalar": "Deleted files",
    "Geçici Dosyalar": "Temporary Files",
    "/tmp altındaki kullanıcınıza ait dosyalar": "Your temporary files under /tmp",
    "Geliştirici Artıkları": "Developer Artifacts",
    "Projelerdeki gereksiz derleme dosyaları (node_modules, __pycache__, vb.)": "Unnecessary build files in projects (node_modules, __pycache__, etc.)",
    "Yinelenen Dosyalar": "Duplicate Files",
    "Aynı içeriğe sahip kopyalar (Masaüstü, Belgeler vb.)": "Copies with identical content (Desktop, Documents, etc.)",
    "Sistem Kategorileri": "System Categories",
    "Kullanıcı Kategorileri": "User Categories",
    "Genel Bakış": "Overview",
    "Sistem Temizleyici": "System Cleaner",
    "Temizleyici": "Cleaner",
    "Sonuçlar": "Results",
    "Detaylı Analiz Et": "Detailed Analysis",
    "Pardus Sistem Temizleyici": "Pardus System Cleaner",
    "Temizleyici": "Cleaner",
    "Dil (Language)": "Language",
    "Türkçe": "Turkish",
    "İngilizce (English)": "English",
    "Lütfen değişikliklerin uygulanması için uygulamayı yeniden başlatın.": "Please restart the application to apply the changes.",
    "2026 Teknofest Pardus Hata Yakalama ve Öneri Yarışması Geliştirme Kategorisi için İnoTürk tarafından geliştirilmiştir.\n\nLinux sisteminizi güvenle temizleyin ve hızlandırın.": "Developed by the InoTurk team for the 2026 Teknofest Pardus Bug Catching and Suggestion Competition.\n\nSecurely clean and speed up your Linux system.",
    "GitHub Reposu": "GitHub Repository",
    "hesaplanıyor...": "calculating...",
    "disk dolu": "disk full",
    "Ana Sayfaya Dön": "Back to Home",
    "Sistem taranıyor...": "Scanning system...",
    "← Geri": "← Back",
    "Tümünü Seç": "Select All",
    "Temizle": "Clean",
    "İşlem İptal Edildi": "Operation Cancelled",
    "Temizleme işlemi tamamlanamadı.": "Cleaning process could not be completed.",
    "Temizlik Geçmişi": "Cleaning History",
    "Henüz temizlik yapılmamış.": "No cleaning done yet.",
    "TOPLAM KAZANILAN": "TOTAL RECOVERED",
    "tüm zamanlar": "all time",
    "TEMİZLİK SAYISI": "CLEAN SESSIONS",
    "oturum": "session",
    "SON TEMİZLİK": "LAST CLEAN",
    "Kategori Bazında Toplam": "Total by Category",
    "Tahmini:": "Estimated:",
    "Tahmini": "Estimated",
    "temizlenebilir": "cleanable",
    "temiz": "clean",
    "yenileniyor...": "refreshing...",
    "Sisteminiz temiz görünüyor": "Your system looks clean",
    "güncel": "up to date",
    "kategori": "categories",
    "alan bulundu": "space found",
    "kategoride alan bulundu": "categories with cleanable space",
    "Temizlenebilecek Alanlar": "Cleanable Space",
    "Liste görünümü": "List view",
    "Kart görünümü": "Card view",
    "kullanılan": "used",
    "boş": "free",
    "Toplam:": "Total:",
    "taranıyor...": "scanning...",
    "Sisteminiz zaten temiz!": "Your system is already clean!",
    "Temizlik Tamamlandı!": "Cleaning Completed!",
    "Temizlik Kısmen Tamamlandı": "Cleaning Partially Completed",
    "Son Temizlikler": "Recent Cleans",
    "İnoTürk tarafından geliştirilmiştir.": "Developed by InoTurk.",
    "Tahmini eski log:": "Estimated old logs:",
    "adet .deb dosyası": "deb files",
    "gereksiz paket": "unnecessary packages",
    "eski çekirdek": "old kernels",
    "önbellek öğesi": "cache items",
    "küçük resim": "thumbnails",
    "çöp dizini/dosyası": "trash files/directories",
    "eski geçici dosya": "old temp files",
    "geliştirici artığı": "developer artifacts",
    "yinelenen dosya grubu": "duplicate file groups",
    "dosya": "files",
    "grup": "groups",
    "kopya": "copies",
    "yinelenen": "duplicates",
    "toplam": "total",
    "Toplam": "Total",
    "alan temizlenecek.": "space will be cleaned.",
    "kategori seçili.": "categories selected.",
    "Bazı işlemler yönetici yetkisi gerektirir.": "Some operations require administrator privileges.",
    "Bu işlem geri alınamaz.": "This operation cannot be undone.",
    "Temizleme Onayı": "Clean Confirmation",
    "İptal": "Cancel",
    "Temizle": "Clean",
    "alan kazanıldı": "space freed",
    "Yönetici izni iptal edildi": "Admin permission canceled"
}

import json

config_dir = os.path.expanduser("~/.config/pardus-temizleyici")
config_path = os.path.join(config_dir, "config.json")
user_lang = None

try:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            user_lang = config.get("language")
except Exception:
    pass

if not user_lang:
    user_lang = "tr_TR"

import builtins
if user_lang and user_lang.startswith("en"):
    builtins._ = lambda text: TRANSLATIONS_EN.get(text, text)
    os.environ["LANGUAGE"] = "en_US.UTF-8"
    os.environ["LC_ALL"] = "en_US.UTF-8"
    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    except locale.Error:
        pass
else:
    builtins._ = lambda text: text
    os.environ["LANGUAGE"] = "tr_TR.UTF-8"
    os.environ["LC_ALL"] = "tr_TR.UTF-8"
    try:
        locale.setlocale(locale.LC_ALL, "tr_TR.UTF-8")
    except locale.Error:
        pass

from application import Application

def main():
    app = Application()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
