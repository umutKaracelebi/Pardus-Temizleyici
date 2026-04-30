"""
Pardus Sistem Temizleyici — Ana Sayfa

İşlevsel ana sayfa:
- Disk kullanım özeti
- Her kategori için gerçek tahmini boyut (dinamik, yenilenebilir)
- Liste / Kart görünüm seçeneği
- Analiz Et butonu
"""

import os
import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from core.categories import CATEGORIES
from core.rules import RuleEngine
from utils.system_info import get_disk_usage
from utils.formatter import format_size


class HomeView(Gtk.Box):
    """İşlevsel ana sayfa — gerçek verilerle, yenilenebilir."""

    def __init__(self, on_scan_clicked=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._on_scan_clicked = on_scan_clicked
        self._view_mode = "card"  # "list" veya "card"
        self.add_css_class("home-view")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._content.set_margin_start(28)
        self._content.set_margin_end(28)
        self._content.set_margin_top(16)
        self._content.set_margin_bottom(24)

        self._build_ui()

        scroll.set_child(self._content)
        self.append(scroll)

        # Arka planda tahmini boyutları hesapla
        self._start_estimation()

    def _build_ui(self):
        """Ana UI'yi oluştur."""
        # ═══ Disk Kullanımı ═══
        self._disk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._disk_box.add_css_class("disk-card")
        self._disk_box.set_margin_bottom(20)
        self._build_disk_card()
        self._content.append(self._disk_box)

        # ═══ Başlık satırı: Temizlenebilecek Alanlar + görünüm butonları ═══
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header_row.set_margin_bottom(10)

        title = Gtk.Label()
        title.set_markup(
            f'<span size="large" weight="bold">{_("Temizlenebilecek Alanlar")}</span>'
        )
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        title.add_css_class("section-title")
        header_row.append(title)

        self._est_status = Gtk.Label(label=_("hesaplanıyor..."))
        self._est_status.add_css_class("est-status")
        self._est_status.set_margin_end(12)
        header_row.append(self._est_status)

        # Görünüm değiştirme butonları
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        view_box.add_css_class("view-toggle")

        self._list_btn = Gtk.Button()
        self._list_btn.set_icon_name("view-list-symbolic")
        self._list_btn.add_css_class("view-btn")
        self._list_btn.set_tooltip_text(_("Liste görünümü"))
        self._list_btn.connect("clicked", self._on_view_toggle, "list")

        self._card_btn = Gtk.Button()
        self._card_btn.set_icon_name("view-grid-symbolic")
        self._card_btn.add_css_class("view-btn")
        self._card_btn.add_css_class("view-btn-active")
        self._card_btn.set_tooltip_text(_("Kart görünümü"))
        self._card_btn.connect("clicked", self._on_view_toggle, "card")

        view_box.append(self._card_btn)
        view_box.append(self._list_btn)
        header_row.append(view_box)

        self._content.append(header_row)

        # ═══ Kategori container — liste veya kart modunda ═══
        self._cat_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._cat_rows = {}
        self._cat_size_labels = {}

        self._build_category_list()
        self._content.append(self._cat_container)

        # ═══ Alt: Toplam + Analiz Et ═══
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        bottom.set_margin_top(18)
        bottom.set_halign(Gtk.Align.CENTER)

        self._total_est = Gtk.Label()
        self._total_est.set_markup(
            f'<span size="large" weight="bold" color="#888">{_("Tahmini:")} ...</span>'
        )
        self._total_est.set_valign(Gtk.Align.CENTER)
        bottom.append(self._total_est)

        analyze_btn = Gtk.Button()
        ac = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ai = Gtk.Image.new_from_icon_name("system-search-symbolic")
        ai.set_pixel_size(20)
        al = Gtk.Label(label=_("Detaylı Analiz Et"))
        al.add_css_class("action-btn-label")
        ac.append(ai)
        ac.append(al)
        analyze_btn.set_child(ac)
        analyze_btn.add_css_class("analyze-button")
        analyze_btn.set_size_request(200, 46)

        if self._on_scan_clicked:
            analyze_btn.connect("clicked", lambda b: self._on_scan_clicked())

        bottom.append(analyze_btn)
        self._content.append(bottom)

    def _build_disk_card(self):
        """Disk kullanım kartını oluştur/yenile."""
        # Temizle
        child = self._disk_box.get_first_child()
        while child:
            nc = child.get_next_sibling()
            self._disk_box.remove(child)
            child = nc

        disk_info = get_disk_usage("/")
        percent = disk_info["percent"]

        # Sol: yüzde
        pct_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        pct_box.set_valign(Gtk.Align.CENTER)
        pct_box.set_margin_end(20)
        pct_box.set_size_request(90, -1)

        pct_label = Gtk.Label()
        pct_label.set_markup(
            f'<span size="28000" weight="bold">%{percent:.0f}</span>'
        )
        pct_label.add_css_class("disk-pct")

        pct_sub = Gtk.Label(label=_("disk dolu"))
        pct_sub.add_css_class("disk-pct-sub")

        pct_box.append(pct_label)
        pct_box.append(pct_sub)
        self._disk_box.append(pct_box)

        # Ayırıcı
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.add_css_class("disk-sep")
        sep.set_margin_top(8)
        sep.set_margin_bottom(8)
        self._disk_box.append(sep)

        # Sağ: detaylar
        disk_details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        disk_details.set_valign(Gtk.Align.CENTER)
        disk_details.set_hexpand(True)
        disk_details.set_margin_start(20)

        pbar = Gtk.ProgressBar()
        pbar.set_fraction(percent / 100)
        if percent < 60:
            pbar.add_css_class("progress-good")
        elif percent < 85:
            pbar.add_css_class("progress-warn")
        else:
            pbar.add_css_class("progress-danger")
        pbar.add_css_class("disk-progress")
        disk_details.append(pbar)

        usage_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        used_lbl = Gtk.Label()
        used_lbl.set_markup(
            f'<span weight="bold">{format_size(disk_info["used"])}</span>'
            f' <span color="#888">{_("kullanılan")}</span>'
        )
        used_lbl.set_halign(Gtk.Align.START)
        used_lbl.set_hexpand(True)
        used_lbl.add_css_class("disk-detail")

        free_lbl = Gtk.Label()
        free_lbl.set_markup(
            f'<span color="#10B981" weight="bold">{format_size(disk_info["free"])}</span>'
            f' <span color="#888">{_("boş")}</span>'
        )
        free_lbl.set_halign(Gtk.Align.END)
        free_lbl.add_css_class("disk-detail")

        usage_row.append(used_lbl)
        usage_row.append(free_lbl)
        disk_details.append(usage_row)

        total_lbl = Gtk.Label()
        total_lbl.set_markup(
            f'<span color="#666">{_("Toplam:")} {format_size(disk_info["total"])}'
            f' · {disk_info.get("fstype", "ext4")}</span>'
        )
        total_lbl.set_halign(Gtk.Align.START)
        total_lbl.add_css_class("disk-total")
        disk_details.append(total_lbl)

        self._disk_box.append(disk_details)

    def _build_category_list(self):
        """Liste modunda kategorileri oluştur."""
        child = self._cat_container.get_first_child()
        while child:
            nc = child.get_next_sibling()
            self._cat_container.remove(child)
            child = nc

        self._cat_size_labels = {}

        if self._view_mode == "list":
            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            for cat in CATEGORIES:
                row = self._make_list_row(cat)
                list_box.append(row)
            self._cat_container.append(list_box)
        else:
            # Kart görünümü — 2 sütun grid
            grid = Gtk.Grid()
            grid.set_row_spacing(10)
            grid.set_column_spacing(10)
            grid.set_column_homogeneous(True)
            for i, cat in enumerate(CATEGORIES):
                card = self._make_card_item(cat)
                grid.attach(card, i % 2, i // 2, 1, 1)
            self._cat_container.append(grid)

    def _make_list_row(self, cat):
        """Liste modunda kategori satırı."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add_css_class("cat-row")

        icon_box = Gtk.Box()
        icon_box.add_css_class("cat-icon-box")
        icon_box.set_size_request(34, 34)
        icon_box.set_valign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name(cat["icon"])
        icon.set_pixel_size(16)
        icon.add_css_class("cat-icon")
        icon_box.append(icon)
        row.append(icon_box)

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        text.set_hexpand(True)
        text.set_valign(Gtk.Align.CENTER)
        name = Gtk.Label(label=cat["name"])
        name.set_halign(Gtk.Align.START)
        name.add_css_class("cat-name")
        desc = Gtk.Label(label=cat["description"])
        desc.set_halign(Gtk.Align.START)
        desc.add_css_class("cat-desc")
        desc.set_ellipsize(3)
        text.append(name)
        text.append(desc)
        row.append(text)

        size_lbl = Gtk.Label(label="—")
        size_lbl.add_css_class("cat-size")
        size_lbl.set_halign(Gtk.Align.END)
        size_lbl.set_width_chars(10)
        row.append(size_lbl)

        self._cat_size_labels[cat["id"]] = size_lbl
        return row

    def _make_card_item(self, cat):
        """Kart modunda kategori kartı."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("cat-card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        icon_box = Gtk.Box()
        icon_box.add_css_class("cat-icon-box")
        icon_box.set_size_request(32, 32)
        icon = Gtk.Image.new_from_icon_name(cat["icon"])
        icon.set_pixel_size(15)
        icon.add_css_class("cat-icon")
        icon_box.append(icon)
        top.append(icon_box)

        name = Gtk.Label(label=cat["name"])
        name.set_halign(Gtk.Align.START)
        name.set_hexpand(True)
        name.add_css_class("cat-name")
        top.append(name)
        card.append(top)

        desc = Gtk.Label(label=cat["description"])
        desc.set_halign(Gtk.Align.START)
        desc.add_css_class("cat-desc")
        desc.set_ellipsize(3)
        card.append(desc)

        size_lbl = Gtk.Label(label="—")
        size_lbl.add_css_class("cat-card-size")
        size_lbl.set_halign(Gtk.Align.START)
        card.append(size_lbl)

        self._cat_size_labels[cat["id"]] = size_lbl
        return card

    def _on_view_toggle(self, btn, mode):
        if mode == self._view_mode:
            return
        self._view_mode = mode

        # Buton aktiflik
        if mode == "list":
            self._list_btn.add_css_class("view-btn-active")
            self._card_btn.remove_css_class("view-btn-active")
        else:
            self._card_btn.add_css_class("view-btn-active")
            self._list_btn.remove_css_class("view-btn-active")

        # Mevcut tahminleri sakla
        saved = {}
        for cid, lbl in self._cat_size_labels.items():
            saved[cid] = lbl.get_text()

        self._build_category_list()

        # Tahminleri geri yükle
        for cid, text in saved.items():
            if cid in self._cat_size_labels:
                lbl = self._cat_size_labels[cid]
                lbl.set_text(text)
                lbl.set_text(text)
                if text not in ("—", _("hesaplanıyor...")):
                    if _("temiz") in text:
                        lbl.add_css_class("cat-size-clean")
                    else:
                        lbl.add_css_class("cat-size-found")

    def refresh(self):
        """Temizlik sonrası verileri yenile."""
        # Disk kartını güncelle
        self._build_disk_card()

        # Tahminleri sıfırla ve yeniden hesapla
        for cid, lbl in self._cat_size_labels.items():
            lbl.set_text("—")
            lbl.remove_css_class("cat-size-found")
            lbl.remove_css_class("cat-size-clean")

        self._est_status.set_text(_("yenileniyor..."))
        self._est_status.remove_css_class("est-done")

        self._total_est.set_markup(
            f'<span size="large" weight="bold" color="#888">{_("Tahmini:")} ...</span>'
        )

        self._start_estimation()

    def _start_estimation(self):
        """Arka planda her kategorinin tahmini boyutunu hesapla."""
        def worker():
            engine = RuleEngine()
            from core.scanner import Scanner
            scanner = Scanner()

            estimates = {}
            for cat in CATEGORIES:
                cat_id = cat["id"]
                try:
                    size = scanner.estimate_category_size(cat_id, engine)
                    estimates[cat_id] = size
                except Exception:
                    estimates[cat_id] = 0
                GLib.idle_add(self._update_cat_size, cat_id, estimates[cat_id])

            total = sum(estimates.values())
            GLib.idle_add(self._update_total, total)

        threading.Thread(target=worker, daemon=True).start()

    def _update_cat_size(self, cat_id, size):
        if cat_id in self._cat_size_labels:
            lbl = self._cat_size_labels[cat_id]
            if size > 0:
                lbl.set_text(format_size(size))
                lbl.add_css_class("cat-size-found")
            else:
                lbl.set_text(_("temiz") + " ✓")
                lbl.add_css_class("cat-size-clean")

    def _update_total(self, total):
        if total > 0:
            self._total_est.set_markup(
                f'<span size="large" weight="bold">'
                f'{_("Tahmini:")} <span color="#3B82F6">{format_size(total)}</span>'
                f' {_("temizlenebilir")}</span>'
            )
        else:
            self._total_est.set_markup(
                f'<span size="large" weight="bold" color="#10B981">'
                f'{_("Sisteminiz temiz görünüyor")} ✨</span>'
            )
        self._est_status.set_text("✓ " + _("güncel"))
        self._est_status.add_css_class("est-done")
