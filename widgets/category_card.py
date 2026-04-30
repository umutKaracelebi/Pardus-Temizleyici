"""
Pardus Sistem Temizleyici — Kategori kartı widget'ı

Glassmorphism tarzında, hover efektli kategori kartı.
Ana ekranda grid olarak gösterilir.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib

from utils.formatter import format_size


class CategoryCard(Gtk.Button):
    """Glassmorphism tarzında kategori kartı."""

    def __init__(self, category, estimated_size=0):
        super().__init__()
        self._category = category
        self._estimated_size = estimated_size

        self.set_css_classes(["category-card"])
        self.set_hexpand(True)
        self.set_vexpand(False)

        # Ana dikey kutu
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)

        # İkon
        icon = Gtk.Image.new_from_icon_name(category["icon"])
        icon.set_pixel_size(40)
        icon.add_css_class("category-icon")

        # Renkli arka plan için CSS sınıfı
        color = category.get("color", "#4A90D9")
        icon_frame = Gtk.Box()
        icon_frame.set_halign(Gtk.Align.CENTER)
        icon_frame.set_size_request(64, 64)
        icon_frame.set_valign(Gtk.Align.CENTER)
        icon_frame.add_css_class("icon-frame")
        icon_frame.append(icon)

        # Kategori adı
        name_label = Gtk.Label(label=category["name"])
        name_label.add_css_class("category-name")
        name_label.set_halign(Gtk.Align.CENTER)

        # Açıklama
        desc_label = Gtk.Label(label=category["description"])
        desc_label.add_css_class("category-desc")
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        desc_label.set_max_width_chars(20)
        desc_label.set_justify(Gtk.Justification.CENTER)

        # Risk etiketi
        risk = category.get("risk", "low")
        risk_map = {
            "low": ("🟢 Güvenli", "risk-low"),
            "medium": ("🟡 Dikkatli", "risk-medium"),
            "high": ("🔴 Riskli", "risk-high"),
        }
        risk_text, risk_class = risk_map.get(risk, risk_map["low"])
        risk_label = Gtk.Label(label=risk_text)
        risk_label.add_css_class("risk-badge")
        risk_label.add_css_class(risk_class)
        risk_label.set_halign(Gtk.Align.CENTER)

        vbox.append(icon_frame)
        vbox.append(name_label)
        vbox.append(desc_label)
        vbox.append(risk_label)

        self.set_child(vbox)

    @property
    def category(self):
        return self._category

    def set_estimated_size(self, size_bytes):
        """Tahmini boyutu güncelle."""
        self._estimated_size = size_bytes
