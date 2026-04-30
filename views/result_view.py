"""
Pardus Sistem Temizleyici — Sonuç Ekranı

İki mod:
1. Sidebar'dan tıklanınca: Tüm zamanların geçmiş istatistikleri (history.json)
2. Temizlik sonrası: Bu sefer ne temizlendi + toplam geçmiş
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from utils.formatter import format_size
from utils.history import get_stats


class ResultView(Gtk.Box):
    """Sonuçlar sayfası — tüm zamanların temizlik geçmişi."""

    def __init__(self, on_home_clicked=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._on_home_clicked = on_home_clicked
        self._last_clean = None  # son temizlik sonuçları
        self.add_css_class("result-view")
        self.set_vexpand(True)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self._outer.set_margin_top(24)
        self._outer.set_margin_bottom(24)
        self._outer.set_margin_start(32)
        self._outer.set_margin_end(32)

        scroll.set_child(self._outer)
        self.append(scroll)

    def refresh(self):
        """Sayfa her görünür olduğunda çağrılır — güncel veriyi gösterir."""
        if self._last_clean:
            self._show_last_clean_with_history()
        else:
            self._show_full_history()

    def show_results(self, clean_results, scan_results):
        """Temizlik sonuçlarını sakla ve göster."""
        self._last_clean = clean_results
        self._show_last_clean_with_history()

    def _show_full_history(self):
        """Tüm zamanların geçmiş istatistiklerini göster."""
        self._clear()

        stats = get_stats()

        # Başlık
        title = Gtk.Label()
        title.set_markup(
            f'<span size="x-large" weight="bold">{_("Temizlik Geçmişi")}</span>'
        )
        title.set_halign(Gtk.Align.START)
        title.add_css_class("result-title")
        self._outer.append(title)

        if stats["total_sessions"] == 0:
            # Boş durum
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            empty_box.set_margin_top(60)
            empty_box.set_halign(Gtk.Align.CENTER)

            empty_icon = Gtk.Label()
            empty_icon.set_markup('<span size="48000">📊</span>')
            empty_box.append(empty_icon)

            empty_title = Gtk.Label()
            empty_title.set_markup(
                f'<span size="large" weight="bold" color="#888">{_("Henüz temizlik yapılmamış.")}</span>'
            )
            empty_box.append(empty_title)

            empty_desc = Gtk.Label()
            text = _("Ana sayfadan \"Detaylı Analiz Et\" butonuyla\nsisteminizi tarayabilir ve temizleyebilirsiniz.")
            empty_desc.set_markup(f'<span color="#666">{text}</span>')
            empty_desc.set_justify(Gtk.Justification.CENTER)
            empty_box.append(empty_desc)

            self._outer.append(empty_box)
            return

        # ─── Toplam İstatistik Kartları ───
        self._append_stat_cards(stats)

        # ─── Kategori bazında toplam ───
        self._append_category_breakdown(stats)

        # ─── Son temizlikler listesi ───
        self._append_session_list(stats)

    def _show_last_clean_with_history(self):
        """Son temizlik sonuçlarını + geçmiş özetini göster."""
        self._clear()
        clean_results = self._last_clean

        total_freed = sum(r.freed_size for r in clean_results.values() if r.success)
        total_errors = sum(1 for r in clean_results.values() if not r.success)

        # Başarı ikonu
        icon = Gtk.Label()
        icon.set_markup(
            '<span size="54000">' +
            ('✨' if total_errors == 0 else '⚠️') +
            '</span>'
        )
        icon.set_halign(Gtk.Align.CENTER)
        self._outer.append(icon)

        title = Gtk.Label()
        title.set_markup(
            '<span size="x-large" weight="bold">' +
            (_('Temizlik Tamamlandı!') if total_errors == 0 else _('Temizlik Kısmen Tamamlandı')) +
            '</span>'
        )
        title.set_halign(Gtk.Align.CENTER)
        title.add_css_class("result-title")
        self._outer.append(title)

        # Kazanılan alan — animasyonlu
        freed_lbl = Gtk.Label()
        freed_lbl.set_halign(Gtk.Align.CENTER)
        freed_lbl.set_margin_top(8)
        self._outer.append(freed_lbl)
        self._animate_counter(freed_lbl, total_freed)

        # Temizlik detayları
        from core.categories import get_category

        detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        detail_box.add_css_class("result-details")
        detail_box.set_margin_top(16)
        detail_box.set_halign(Gtk.Align.CENTER)

        for cat_id, result in clean_results.items():
            cat = get_category(cat_id)
            name = cat["name"] if cat else cat_id

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_start(8)
            row.set_margin_end(8)

            status = "✅" if result.success else "❌"
            lbl = Gtk.Label(label=f"{status}  {name}")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_hexpand(True)
            lbl.add_css_class("detail-name")

            val = format_size(result.freed_size) if result.success else result.error
            val_lbl = Gtk.Label(label=val)
            val_lbl.add_css_class("detail-size" if result.success else "detail-error")

            row.append(lbl)
            row.append(val_lbl)
            detail_box.append(row)

        self._outer.append(detail_box)

        # ─── Geçmiş özeti ───
        sep = Gtk.Separator()
        sep.set_margin_top(20)
        sep.set_margin_bottom(8)
        sep.add_css_class("result-sep")
        self._outer.append(sep)

        stats = get_stats()
        self._append_stat_cards(stats)

        # ─── Butonlar ───
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(16)

        home_btn = Gtk.Button()
        hc = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hi = Gtk.Image.new_from_icon_name("go-home-symbolic")
        hl = Gtk.Label(label=_("Ana Sayfaya Dön"))
        hc.append(hi)
        hc.append(hl)
        home_btn.set_child(hc)
        home_btn.add_css_class("home-button")
        home_btn.set_size_request(200, 44)

        if self._on_home_clicked:
            home_btn.connect("clicked", lambda b: self._on_home_clicked())

        btn_box.append(home_btn)
        self._outer.append(btn_box)

    def _append_stat_cards(self, stats):
        """3 istatistik kartı ekle."""
        cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        cards.set_homogeneous(True)
        cards.set_margin_top(8)

        cards.append(self._make_stat_card(
            _("TOPLAM KAZANILAN"),
            format_size(stats["total_freed"]),
            _("tüm zamanlar"),
            "#10B981"
        ))

        cards.append(self._make_stat_card(
            _("TEMİZLİK SAYISI"),
            str(stats["total_sessions"]),
            _("oturum"),
            "#3B82F6"
        ))

        cards.append(self._make_stat_card(
            _("SON TEMİZLİK"),
            stats["last_clean"],
            "",
            "#F59E0B"
        ))

        self._outer.append(cards)

    def _append_category_breakdown(self, stats):
        """Kategori bazında toplam temizlenen."""
        if not stats["category_totals"]:
            return

        cat_title = Gtk.Label()
        cat_title.set_markup(
            f'<span size="large" weight="bold">{_("Kategori Bazında Toplam")}</span>'
        )
        cat_title.set_halign(Gtk.Align.START)
        cat_title.set_margin_top(16)
        self._outer.append(cat_title)

        from core.categories import get_category

        sorted_cats = sorted(
            stats["category_totals"].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for cat_id, total_size in sorted_cats:
            cat = get_category(cat_id)
            name = cat["name"] if cat else cat_id

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.add_css_class("history-row")

            icon = Gtk.Image.new_from_icon_name(
                cat["icon"] if cat else "folder-symbolic"
            )
            icon.set_pixel_size(20)
            icon.add_css_class("history-row-icon")

            lbl = Gtk.Label(label=name)
            lbl.set_halign(Gtk.Align.START)
            lbl.set_hexpand(True)
            lbl.add_css_class("history-row-name")

            size_lbl = Gtk.Label(label=format_size(total_size))
            size_lbl.add_css_class("history-row-size")

            row.append(icon)
            row.append(lbl)
            row.append(size_lbl)
            self._outer.append(row)

    def _append_session_list(self, stats):
        """Son temizlik oturumları listesi."""
        from utils.history import load_history

        history = load_history()
        if len(history) < 2:
            return

        session_title = Gtk.Label()
        session_title.set_markup(
            f'<span size="large" weight="bold">{_("Son Temizlikler")}</span>'
        )
        session_title.set_halign(Gtk.Align.START)
        session_title.set_margin_top(16)
        self._outer.append(session_title)

        # Son 10 oturum (tersten)
        for record in reversed(history[-10:]):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.add_css_class("history-row")

            date_lbl = Gtk.Label(label=record.get("date", "—"))
            date_lbl.set_halign(Gtk.Align.START)
            date_lbl.set_hexpand(True)
            date_lbl.add_css_class("history-row-name")

            size_lbl = Gtk.Label(
                label=format_size(record.get("total_freed", 0))
            )
            size_lbl.add_css_class("history-row-size")

            cats = len(record.get("categories", {}))
            cat_lbl = Gtk.Label(label=f"{cats} {_('kategori')}")
            cat_lbl.add_css_class("history-row-cat")

            row.append(date_lbl)
            row.append(cat_lbl)
            row.append(size_lbl)
            self._outer.append(row)

    def _make_stat_card(self, title, value, subtitle, color):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("stat-mini-card")

        t = Gtk.Label(label=title)
        t.add_css_class("stat-mini-title")
        t.set_halign(Gtk.Align.START)

        v = Gtk.Label()
        v.set_markup(
            f'<span size="18000" weight="bold" color="{color}">{value}</span>'
        )
        v.set_halign(Gtk.Align.START)

        s = Gtk.Label(label=subtitle)
        s.add_css_class("stat-mini-sub")
        s.set_halign(Gtk.Align.START)

        card.append(t)
        card.append(v)
        if subtitle:
            card.append(s)
        return card

    def _animate_counter(self, label, target):
        self._anim_current = 0
        self._anim_target = target

        def step():
            diff = self._anim_target - self._anim_current
            if abs(diff) < 1024:
                self._anim_current = self._anim_target
                label.set_markup(
                    f'<span size="30000" weight="ultrabold" color="#10B981">'
                    f'{format_size(self._anim_target)}</span>'
                    f'\n<span size="12000" color="#888">{_("alan kazanıldı")}</span>'
                )
                return False
            self._anim_current += diff * 0.08
            label.set_markup(
                f'<span size="30000" weight="ultrabold" color="#10B981">'
                f'{format_size(int(self._anim_current))}</span>'
                f'\n<span size="12000" color="#888">{_("alan kazanıldı")}</span>'
            )
            return True

        label.set_markup(
            '<span size="30000" weight="ultrabold" color="#10B981">0 B</span>'
            f'\n<span size="12000" color="#888">{_("alan kazanıldı")}</span>'
        )
        GLib.timeout_add(20, step)

    def _clear(self):
        child = self._outer.get_first_child()
        while child:
            nc = child.get_next_sibling()
            self._outer.remove(child)
            child = nc
