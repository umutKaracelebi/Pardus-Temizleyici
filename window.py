"""
Pardus Sistem Temizleyici — Ana Pencere

Yatay layout: Sol sidebar navigasyon + Sağ içerik.
Sade ve işlevsel.
"""

import os
import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, GdkPixbuf

from views.home_view import HomeView
from views.scan_view import ScanView
from views.result_view import ResultView
from core.scanner import Scanner
from core.cleaner import Cleaner
from utils.formatter import format_size


class MainWindow(Adw.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._app_dir = os.path.dirname(os.path.abspath(__file__))
        self._logo_path = os.path.join(self._app_dir, "pardus-temizleyici.png")

        self.set_title("Pardus Sistem Temizleyici")
        self.set_default_size(1050, 660)
        self.set_size_request(860, 500)

        self._scanner = Scanner()
        self._cleaner = Cleaner()
        self._scan_results = {}

        # Kök: headerbar + yatay içerik
        toolbar = Adw.ToolbarView()

        hb = Adw.HeaderBar()
        hb.add_css_class("flat")
        hb.set_title_widget(Gtk.Label())
        hb.set_show_title(False)
        about_btn = Gtk.Button.new_from_icon_name("help-about-symbolic")
        about_btn.add_css_class("flat")
        about_btn.set_tooltip_text("Hakkında")
        about_btn.connect("clicked", self._on_about)
        hb.pack_end(about_btn)
        toolbar.add_top_bar(hb)

        # Yatay: sidebar + içerik
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        sidebar = self._build_sidebar()
        hbox.append(sidebar)

        # İçerik stack
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)
        self._stack.set_hexpand(True)

        self._home_view = HomeView(on_scan_clicked=self._start_scan)
        self._scan_view = ScanView(
            on_clean_clicked=self._start_clean,
            on_back_clicked=self._go_home
        )
        self._result_view = ResultView(on_home_clicked=self._go_home)

        self._stack.add_named(self._home_view, "home")
        self._stack.add_named(self._scan_view, "scan")
        self._stack.add_named(self._result_view, "result")

        hbox.append(self._stack)
        toolbar.set_content(hbox)
        self.set_content(toolbar)

    def _build_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar.set_size_request(210, -1)
        sidebar.add_css_class("sidebar")

        # Logo + isim
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand.set_margin_top(20)
        brand.set_margin_bottom(28)
        brand.set_margin_start(18)
        brand.set_margin_end(18)

        if os.path.exists(self._logo_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                self._logo_path, 36, 36, True
            )
            logo = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            logo = Gtk.Image.new_from_icon_name("brush-symbolic")
            logo.set_pixel_size(32)

        brand.append(logo)

        brand_text = Gtk.Label()
        brand_text.set_markup(
            '<span weight="bold" size="large">Temizleyici</span>'
        )
        brand_text.add_css_class("sidebar-brand")
        brand.append(brand_text)
        sidebar.append(brand)

        # Navigasyon
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        nav.set_margin_start(10)
        nav.set_margin_end(10)

        self._nav_buttons = {}
        self._page_titles = {
            "home": "Genel Bakış",
            "scan": "Sistem Temizleyici",
            "result": "Sonuçlar",
        }

        for vid, icon, label in [
            ("home", "go-home-symbolic", "Genel Bakış"),
            ("scan", "edit-delete-symbolic", "Temizleyici"),
            ("result", "emblem-ok-symbolic", "Sonuçlar"),
        ]:
            btn = Gtk.Button()
            btn.add_css_class("nav-button")

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            ic = Gtk.Image.new_from_icon_name(icon)
            ic.set_pixel_size(17)
            ic.add_css_class("nav-icon")
            lb = Gtk.Label(label=label)
            lb.set_halign(Gtk.Align.START)
            lb.add_css_class("nav-label")

            row.append(ic)
            row.append(lb)
            btn.set_child(row)
            btn.connect("clicked", self._on_nav, vid)

            nav.append(btn)
            self._nav_buttons[vid] = btn

        sidebar.append(nav)

        # Boşluk
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar.append(spacer)

        self._active_nav = "home"
        self._nav_buttons["home"].add_css_class("nav-active")

        return sidebar

    def _on_nav(self, btn, vid):
        if vid == "scan" and self._stack.get_visible_child_name() == "home":
            self._start_scan()
            return
        self._switch_to(vid)

    def _switch_to(self, vid):
        if self._active_nav in self._nav_buttons:
            self._nav_buttons[self._active_nav].remove_css_class("nav-active")
        self._active_nav = vid
        if vid in self._nav_buttons:
            self._nav_buttons[vid].add_css_class("nav-active")
        self._stack.set_visible_child_name(vid)

        # Sayfa göründüğünde verileri yenile
        if vid == "home":
            self._home_view.refresh()
        elif vid == "result":
            self._result_view.refresh()

    def _go_home(self):
        self._switch_to("home")

    def _start_scan(self):
        self._scan_view.reset()
        self._switch_to("scan")

        def progress_cb(cat_id, current, total):
            GLib.idle_add(self._scan_view.update_progress, cat_id, current, total)

        def done_cb(results):
            self._scan_results = results
            GLib.idle_add(self._scan_view.show_results, results)

        thread = threading.Thread(
            target=self._scanner.scan_all,
            kwargs={"progress_callback": progress_cb, "done_callback": done_cb},
            daemon=True
        )
        thread.start()

    def _start_clean(self, results):
        selected = {}
        for k, v in results.items():
            if v.selected and v.total_size > 0:
                # selected_size hesapla (dosya bazlı seçim)
                sel_size = v.selected_size
                if sel_size > 0:
                    selected[k] = v

        if not selected:
            return

        total = sum(r.selected_size for r in selected.values())
        root = any(
            r.category_id in ("apt_cache", "apt_autoremove", "old_kernels", "journal_logs")
            for r in selected.values()
        )

        msg = f"Toplam {format_size(total)} alan temizlenecek.\n{len(selected)} kategori seçili.\n"
        if root:
            msg += "\n⚠️ Bazı işlemler yönetici yetkisi gerektirir."
        msg += "\n\nBu işlem geri alınamaz."

        dialog = Adw.MessageDialog(
            transient_for=self, heading="Temizleme Onayı", body=msg
        )
        dialog.add_response("cancel", "İptal")
        dialog.add_response("clean", "Temizle")
        dialog.set_response_appearance("clean", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_confirm, selected)
        dialog.present()

    def _on_confirm(self, dialog, response, selected):
        if response != "clean":
            # İptal edildi — scan sayfasında kal, hiçbir şey yapma
            return

        def done_cb(cr):
            from utils.history import save_clean_record

            total_freed = sum(r.freed_size for r in cr.values() if r.success)

            if total_freed > 0:
                save_clean_record(cr)

            # Her zaman sonuçları göster (kısmi başarı da olsa)
            GLib.idle_add(self._result_view.show_results, cr, self._scan_results)
            GLib.idle_add(self._switch_to, "result")

        threading.Thread(
            target=self._cleaner.clean_selected,
            args=(selected,),
            kwargs={"done_callback": done_cb},
            daemon=True
        ).start()

    def _show_cancel_message(self, clean_results):
        """Temizleme başarısız olduğunda bilgi göster."""
        errors = [r.error for r in clean_results.values() if not r.success and r.error]
        msg = errors[0] if errors else "Temizleme işlemi tamamlanamadı."

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="İşlem İptal Edildi",
            body=msg
        )
        dialog.add_response("ok", "Tamam")
        dialog.present()

    def _on_about(self, btn):
        Adw.AboutWindow(
            transient_for=self,
            application_name="Pardus Sistem Temizleyici",
            application_icon="pardus-temizleyici",
            developer_name="Pardus Topluluk",
            version="1.0.0",
            comments="Linux sisteminizi temiz ve hızlı tutun.\nGüvenli, kural tabanlı temizleme motoru.",
            license_type=Gtk.License.GPL_3_0,
        ).present()
