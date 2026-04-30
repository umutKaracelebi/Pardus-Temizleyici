"""
Pardus Sistem Temizleyici — Tarama ve Temizleme Görünümü

Tarama ilerlemesi, sonuçlar listesi, seçim ve temizle butonları.
İlerleme çubuğu ile temizleme süreci gösterimi.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from widgets.scan_row import ScanRow
from widgets.circular_progress import CircularProgress
from core.categories import get_category
from utils.formatter import format_size


class ScanView(Gtk.Box):
    """Tarama sonuçları görünümü."""

    def __init__(self, on_clean_clicked=None, on_back_clicked=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._on_clean_clicked = on_clean_clicked
        self._on_back_clicked = on_back_clicked
        self._scan_rows = []
        self._results = {}
        self.add_css_class("scan-view")

        # ─── Üst: Tarama durumu ───
        self._header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._header_box.set_margin_top(24)
        self._header_box.set_margin_bottom(16)
        self._header_box.set_margin_start(32)
        self._header_box.set_margin_end(32)

        # Tarama sırasında: ilerleme
        self._scanning_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._scanning_box.set_halign(Gtk.Align.CENTER)
        self._scanning_box.set_valign(Gtk.Align.CENTER)

        self._scan_progress = CircularProgress(size=120, line_width=8)
        self._scan_progress.set_halign(Gtk.Align.CENTER)
        self._scan_progress.set_text("0%")
        self._scan_progress.set_sub_text(_("taranıyor..."))
        self._scan_progress.start_pulse()

        self._scan_status = Gtk.Label(label=_("Sistem taranıyor..."))
        self._scan_status.add_css_class("scan-status")

        # İlerleme çubuğu
        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.add_css_class("scan-progress-bar")
        self._progress_bar.set_margin_start(60)
        self._progress_bar.set_margin_end(60)

        self._scanning_box.append(self._scan_progress)
        self._scanning_box.append(self._scan_status)
        self._scanning_box.append(self._progress_bar)
        self._header_box.append(self._scanning_box)

        # Tamamlandığında: özet
        self._summary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self._summary_box.set_halign(Gtk.Align.CENTER)
        self._summary_box.set_visible(False)

        self._total_label = Gtk.Label()
        self._total_label.add_css_class("scan-total")

        self._count_label = Gtk.Label()
        self._count_label.add_css_class("scan-count")

        info_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_col.set_valign(Gtk.Align.CENTER)
        info_col.append(self._total_label)
        info_col.append(self._count_label)
        self._summary_box.append(info_col)
        self._header_box.append(self._summary_box)

        self.append(self._header_box)

        # ─── Sonuçlar ───
        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroll.set_vexpand(True)

        self._results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._results_box.set_margin_start(32)
        self._results_box.set_margin_end(32)
        self._results_box.set_margin_bottom(12)
        self._scroll.set_child(self._results_box)
        self.append(self._scroll)

        # ─── Alt butonlar ───
        self._button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._button_box.set_halign(Gtk.Align.CENTER)
        self._button_box.set_margin_top(8)
        self._button_box.set_margin_bottom(20)
        self._button_box.set_visible(False)

        back_btn = Gtk.Button(label=_("← Geri"))
        back_btn.add_css_class("back-button")
        back_btn.set_size_request(120, 42)
        if on_back_clicked:
            back_btn.connect("clicked", lambda b: on_back_clicked())

        select_all_btn = Gtk.Button(label=_("Tümünü Seç"))
        select_all_btn.add_css_class("select-all-button")
        select_all_btn.set_size_request(120, 42)
        select_all_btn.connect("clicked", self._on_select_all)

        self._clean_btn = Gtk.Button()
        clean_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        clean_content.set_halign(Gtk.Align.CENTER)
        clean_content.set_valign(Gtk.Align.CENTER)
        clean_icon = Gtk.Image.new_from_icon_name("edit-clear-all-symbolic")
        clean_label = Gtk.Label(label=_("Temizle"))
        clean_label.add_css_class("clean-btn-label")
        clean_content.append(clean_icon)
        clean_content.append(clean_label)
        self._clean_btn.set_child(clean_content)
        self._clean_btn.add_css_class("clean-button")
        self._clean_btn.add_css_class("destructive-action")
        self._clean_btn.set_size_request(160, 46)
        if on_clean_clicked:
            self._clean_btn.connect("clicked", lambda b: on_clean_clicked(self._results))

        self._button_box.append(back_btn)
        self._button_box.append(select_all_btn)
        self._button_box.append(self._clean_btn)
        self.append(self._button_box)

    def update_progress(self, category_id, current, total):
        """Tarama ilerlemesini güncelle."""
        percent = current / total if total > 0 else 0
        category = get_category(category_id)
        name = category["name"] if category else category_id

        self._scan_progress.set_progress(percent)
        self._scan_progress.set_text(f"%{int(percent * 100)}")
        self._scan_status.set_text(f"{name} {_('taranıyor...')}")
        self._progress_bar.set_fraction(percent)

    def show_results(self, results):
        """Tarama sonuçlarını göster."""
        self._results = results
        self._scan_rows = []

        self._scanning_box.set_visible(False)
        self._scan_progress.stop_pulse()
        self._summary_box.set_visible(True)
        self._button_box.set_visible(True)

        total_size = sum(r.total_size for r in results.values())
        total_categories = sum(1 for r in results.values() if r.total_size > 0)

        self._total_label.set_markup(
            f'<span size="xx-large" weight="bold">{format_size(total_size)}</span>'
            f'  <span size="large" color="#888">{_("temizlenebilir")}</span>'
        )
        self._count_label.set_text(
            f"{total_categories} {_('kategoride alan bulundu')}"
        )

        # Temizle
        child = self._results_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._results_box.remove(child)
            child = next_child

        sorted_results = sorted(
            results.values(),
            key=lambda r: r.total_size,
            reverse=True
        )

        for result in sorted_results:
            if result.total_size > 0:
                row = ScanRow(result)
                self._scan_rows.append(row)
                self._results_box.append(row)

        if not self._scan_rows:
            empty_label = Gtk.Label()
            empty_label.set_markup(
                f'<span size="large">✨ {_("Sisteminiz zaten temiz!")}</span>'
            )
            empty_label.add_css_class("empty-results")
            self._results_box.append(empty_label)
            self._clean_btn.set_sensitive(False)

    def _on_select_all(self, btn):
        all_selected = all(row.scan_result.selected for row in self._scan_rows)
        for row in self._scan_rows:
            row.scan_result.selected = not all_selected
            row._check.set_active(not all_selected)

    def reset(self):
        self._scanning_box.set_visible(True)
        self._summary_box.set_visible(False)
        self._button_box.set_visible(False)
        self._scan_progress.set_progress(0, animate=False)
        self._scan_progress.set_text("0%")
        self._scan_progress.set_sub_text(_("taranıyor..."))
        self._scan_progress.start_pulse()
        self._scan_status.set_text(_("Sistem taranıyor..."))
        self._progress_bar.set_fraction(0)

        child = self._results_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._results_box.remove(child)
            child = next_child
