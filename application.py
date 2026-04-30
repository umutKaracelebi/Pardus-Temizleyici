"""
Pardus Sistem Temizleyici — Adw.Application

Uygulama yaşam döngüsü, CSS yükleme ve renk şeması yönetimi.
"""

import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib

from window import MainWindow


class Application(Adw.Application):
    """Ana uygulama sınıfı."""

    def __init__(self):
        super().__init__(
            application_id="com.pardus.temizleyici",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.set_resource_base_path("/com/pardus/temizleyici")

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Logoyu GTK'nın bulabilmesi için ana dizini ikon arama yoluna ekle
        app_dir = os.path.dirname(os.path.abspath(__file__))
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_theme.add_search_path(app_dir)

        # Koyu tema varsayılan
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        # CSS yükle
        self._load_css()

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = MainWindow(application=self)
        win.present()

    def _load_css(self):
        """Özel CSS dosyasını yükle."""
        css_provider = Gtk.CssProvider()

        # CSS dosyasının yolunu bul
        app_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(app_dir, "data", "style.css")

        if os.path.exists(css_path):
            css_provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
