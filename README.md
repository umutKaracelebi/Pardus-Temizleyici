# Pardus Sistem Temizleyici 🧹

2026 Teknofest Pardus Hata Yakalama ve Öneri Yarışması Geliştirme Kategorisi için **İnoTürk** takımı tarafından geliştirilmiştir.

## Hakkında
Pardus Sistem Temizleyici, modern, güvenli ve kullanıcı dostu bir Linux sistem temizleme aracıdır. Geleneksel temizleyicilerin aksine, körü körüne tüm sistemi silmek yerine **kural tabanlı, akıllı ve şeffaf** bir temizlik motoru kullanır. Sisteminizin ihtiyacı olmayan kalıntıları silerken, sistemin çalışmasını bozabilecek hiçbir dosyaya dokunmaz.

[English Documentation (README_EN.md)](README_EN.md)

## Öne Çıkan Özellikler

*   🛡️ **Sıfır Riskli Kural Motoru**: Ne sileceğini net olarak belirten kurallarla (RuleEngine) çalışır.
*   🔒 **Akıllı Yönetici (Root) Yetkisi**: Yalnızca `apt-get clean` veya `journalctl` gibi sistem seviyesinde işlem yapılacağı zaman şifre ister. Kullanıcı verileri (Önbellek, Geri Dönüşüm Kutusu) temizlenirken asla root yetkisi istemez. İşlem iptal edilirse, yetki gerektirmeyen diğer dosyaları güvenle temizlemeye devam eder.
*   👯 **Gelişmiş Yinelenen Dosya Bulucu**: XDG standartlarına (Masaüstü, Belgeler, İndirilenler vb.) uyarak sadece kullanıcının şahsi klasörlerini tarar. Geliştirici SDK'larına (Android, node_modules) veya gizli `.cache` klasörlerine sızarak sistemi bozmaz. Eşleşmelerde isimlere değil, MD5 hash yardımıyla doğrudan dosya **içeriğine** bakar.
*   🎨 **Modern GTK4 & Libadwaita Arayüzü**: Karanlık tema uyumlu, animasyonlu, kart ve liste görünümü sunan akıcı kullanıcı deneyimi.
*   🌍 **Çift Dil Desteği**: Sistem dilinize göre Türkçe ve İngilizce dilleri arasında otomatik geçiş yapar.

## Kurulum ve Çalıştırma

### .deb Paketi İle Kurulum (Önerilen)
Uygulamayı sisteminize tam entegre (uygulama menüsü, simgeler vb.) olarak kurmak için GitHub Releases bölümünden güncel `.deb` paketini indirin ve terminalden şu komutla kurun:
```bash
sudo dpkg -i pardus-temizleyici_1.0.0_all.deb
sudo apt install -f  # (Eksik bağımlılıkları otomatik kurmak için)
```
Kurulum bittikten sonra uygulamayı Pardus Uygulamalar menüsünden simgesine tıklayarak başlatabilir veya terminale `pardus-temizleyici` yazabilirsiniz.

### Kaynak Koddan Çalıştırma (Geliştiriciler İçin)
Uygulamayı doğrudan kodlar üzerinden test etmek isterseniz şu sistem paketlerinin kurulu olduğundan emin olun:
- Python 3.x, `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `pkexec`

Ardından terminalden proje dizinine girip çalıştırın:
```bash
python3 main.py
```

## Güvenlik Altyapısı
Pardus Sistem Temizleyici, komut enjeksiyonlarına (command injection) karşı güvenlidir. Kullanıcı dosyaları doğrudan Python'un `os` ve `shutil` kütüphaneleriyle silinir. Sistem görevleri (apt-get, journalctl) ise parçalanmış diziler (array) olarak izole bir şekilde arka planda yönetilir.

## Lisans
Bu proje açık kaynak kodlu olup GPL-3.0 lisansı ile korunmaktadır. Özgürce kullanılabilir, geliştirilebilir ve dağıtılabilir.
