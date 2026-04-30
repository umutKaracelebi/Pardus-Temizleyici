"""
Pardus Sistem Temizleyici — Tarama sonuç satırı widget'ı

Her kategori için genişletilebilir, checkbox'lu sonuç satırı.
Dosya bazında seçim/kaldırma desteği.
Yinelenen dosyalar için özel grup bazlı arayüz.
"""

import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from core.categories import get_category
from utils.formatter import format_size


class ScanRow(Gtk.Box):
    """Tarama sonucu kategori satırı — dosya bazlı seçimli."""

    def __init__(self, scan_result):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._scan_result = scan_result
        self._expanded = False
        self._file_checks = []
        self._batch_update = False
        self.add_css_class("scan-row")

        category = get_category(scan_result.category_id)
        if not category:
            return

        # ─── Ana satır ───
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_top(12)
        header.set_margin_bottom(12)
        header.set_margin_start(16)
        header.set_margin_end(16)

        # Checkbox
        self._check = Gtk.CheckButton()
        self._check.set_active(scan_result.selected)
        self._check.connect("toggled", self._on_toggled)

        # İkon
        icon = Gtk.Image.new_from_icon_name(category["icon"])
        icon.set_pixel_size(28)
        icon.add_css_class("scan-row-icon")

        # Bilgi
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        name_label = Gtk.Label(label=category["name"])
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("scan-row-name")

        details_label = Gtk.Label(label=scan_result.details)
        details_label.set_halign(Gtk.Align.START)
        details_label.add_css_class("scan-row-details")

        info_box.append(name_label)
        info_box.append(details_label)

        # Boyut
        self._size_label = Gtk.Label(label=format_size(scan_result.total_size))
        self._size_label.add_css_class("scan-row-size")

        # Genişlet butonu
        self._expand_btn = Gtk.Button()
        self._expand_btn.set_icon_name("pan-down-symbolic")
        self._expand_btn.add_css_class("flat")
        self._expand_btn.add_css_class("expand-btn")
        self._expand_btn.connect("clicked", self._on_expand)

        header.append(self._check)
        header.append(icon)
        header.append(info_box)
        header.append(self._size_label)
        if scan_result.files or hasattr(scan_result, 'duplicate_groups'):
            header.append(self._expand_btn)

        self.append(header)

        # ─── Genişletilebilir alan ───
        self._detail_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._detail_wrapper.set_margin_start(56)
        self._detail_wrapper.set_margin_end(16)
        self._detail_wrapper.set_margin_bottom(8)
        self._detail_wrapper.set_visible(False)

        if scan_result.category_id == "duplicates" and hasattr(scan_result, 'duplicate_groups'):
            self._build_duplicate_groups(scan_result)
        else:
            self._build_flat_file_list(scan_result)

        self.append(self._detail_wrapper)

    def _build_flat_file_list(self, scan_result):
        """Normal kategoriler için düz dosya listesi."""
        count_lbl = Gtk.Label(label=f"{len(scan_result.files)} {_('dosya')}")
        count_lbl.set_halign(Gtk.Align.START)
        count_lbl.add_css_class("file-count-label")
        count_lbl.set_margin_bottom(4)
        self._detail_wrapper.append(count_lbl)

        file_scroll = Gtk.ScrolledWindow()
        file_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        file_scroll.set_min_content_height(min(len(scan_result.files) * 36, 250))
        file_scroll.set_max_content_height(250)
        file_scroll.set_propagate_natural_height(True)

        detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        detail_box.add_css_class("scan-detail-box")

        for i, (filepath, size) in enumerate(scan_result.files):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            file_check = Gtk.CheckButton()
            file_check.set_active(True)
            file_check.connect("toggled", self._on_file_toggled, i)
            self._file_checks.append(file_check)

            name = os.path.basename(filepath) if "/" in filepath else filepath
            file_label = Gtk.Label(label=name)
            file_label.set_halign(Gtk.Align.START)
            file_label.set_hexpand(True)
            file_label.set_ellipsize(3)
            file_label.add_css_class("file-item-name")
            file_label.set_tooltip_text(filepath)

            file_size = Gtk.Label(label=format_size(size))
            file_size.add_css_class("file-item-size")

            row.append(file_check)
            row.append(file_label)
            row.append(file_size)
            detail_box.append(row)

        file_scroll.set_child(detail_box)
        self._detail_wrapper.append(file_scroll)

    def _build_duplicate_groups(self, scan_result):
        """Yinelenen dosyalar için grup bazlı arayüz."""
        groups = scan_result.duplicate_groups

        count_lbl = Gtk.Label(label=f"{len(groups)} {_('grup')} · {len(scan_result.files)} {_('kopya')}")
        count_lbl.set_halign(Gtk.Align.START)
        count_lbl.add_css_class("file-count-label")
        count_lbl.set_margin_bottom(6)
        self._detail_wrapper.append(count_lbl)

        file_scroll = Gtk.ScrolledWindow()
        file_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        calc_h = (len(groups) * 35) + (len(scan_result.files) * 36)
        file_scroll.set_min_content_height(min(calc_h, 300))
        file_scroll.set_max_content_height(300)
        file_scroll.set_propagate_natural_height(True)

        groups_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # files listesindeki indeksi takip et
        file_idx = 0

        for group in groups:
            g_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            g_box.add_css_class("dup-group")

            # Grup başlığı
            g_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            g_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
            g_icon.set_pixel_size(14)
            g_icon.add_css_class("dup-group-icon")

            g_name = Gtk.Label()
            g_name.set_markup(
                f'<b>{group["name"]}</b>'
                f'  <span color="#888" size="small">'
                f'{format_size(group["size"])} × {len(group["paths"])} kopya</span>'
            )
            g_name.set_halign(Gtk.Align.START)
            g_name.set_hexpand(True)
            g_name.add_css_class("dup-group-name")

            g_header.append(g_icon)
            g_header.append(g_name)
            g_box.append(g_header)

            # Kopyalar listesi
            for j, path in enumerate(group["paths"]):
                p_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                p_row.set_margin_start(22)

                # Checkbox durumu scan_result.file_selected üzerinden alınır
                # Önceden ilk eleman (j==0) unchecked olarak işaretlendi
                is_selected = self._scan_result.file_selected[file_idx]

                file_check = Gtk.CheckButton()
                file_check.set_active(is_selected)
                self._file_checks.append(file_check)
                p_row.append(file_check)

                # Tam dosya yolunu göster
                p_label = Gtk.Label(label=path)
                p_label.set_halign(Gtk.Align.START)
                p_label.set_hexpand(True)
                p_label.set_ellipsize(3)
                p_label.set_tooltip_text(path)
                
                tag = Gtk.Label()
                p_row.append(p_label)
                p_row.append(tag)

                # Helper fonksiyon - toggle durumuna göre stilleri günceller
                def update_row_style(check, lbl=p_label, t=tag):
                    if check.get_active():
                        lbl.remove_css_class("dup-path-keep")
                        lbl.add_css_class("dup-path-delete")
                        t.set_text("SİLİNECEK")
                        t.remove_css_class("dup-tag-keep")
                        t.add_css_class("dup-tag-delete")
                    else:
                        lbl.remove_css_class("dup-path-delete")
                        lbl.add_css_class("dup-path-keep")
                        t.set_text("KORUNACAK")
                        t.remove_css_class("dup-tag-delete")
                        t.add_css_class("dup-tag-keep")

                # İlk stili uygula
                update_row_style(file_check)

                # Toggled event bağlantısı
                file_check.connect("toggled", lambda c, l=p_label, t=tag, idx=file_idx: 
                                   (update_row_style(c, l, t), self._on_file_toggled(c, idx)))

                file_idx += 1
                g_box.append(p_row)

            groups_box.append(g_box)

        file_scroll.set_child(groups_box)
        self._detail_wrapper.append(file_scroll)

    def _on_toggled(self, check):
        """Kategori checkbox — tümünü seç/kaldır."""
        active = check.get_active()
        self._scan_result.selected = active

        # Batch: sinyal geri çağrılarını engelle
        self._batch_update = True
        for i, fc in enumerate(self._file_checks):
            if i < len(self._scan_result.file_selected):
                self._scan_result.file_selected[i] = active
            fc.set_active(active)
        self._batch_update = False

        self._update_size_label()

    def _on_file_toggled(self, check, index):
        """Tekil dosya checkbox'ı."""
        if self._batch_update:
            return  # Batch güncelleme sırasında atla

        if index < len(self._scan_result.file_selected):
            self._scan_result.file_selected[index] = check.get_active()
        self._update_size_label()

        any_selected = any(self._scan_result.file_selected)
        if not any_selected and self._check.get_active():
            self._check.set_active(False)
        elif any_selected and not self._check.get_active():
            self._check.set_active(True)

    def _update_size_label(self):
        """Boyut etiketini güncelle — asla 0B gösterme."""
        total = self._scan_result.total_size
        sel = self._scan_result.selected_size

        # Önce tüm durum sınıflarını temizle
        self._size_label.remove_css_class("size-partial")
        self._size_label.remove_css_class("size-deselected")

        if sel == total:
            self._size_label.set_text(format_size(total))
        elif sel == 0:
            self._size_label.set_text(format_size(total))
            self._size_label.add_css_class("size-deselected")
        else:
            self._size_label.set_text(format_size(sel))
            self._size_label.add_css_class("size-partial")

    def _on_expand(self, btn):
        self._expanded = not self._expanded
        self._detail_wrapper.set_visible(self._expanded)
        self._expand_btn.set_icon_name(
            "pan-up-symbolic" if self._expanded else "pan-down-symbolic"
        )

    @property
    def scan_result(self):
        return self._scan_result
