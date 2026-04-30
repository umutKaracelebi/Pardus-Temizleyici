"""
Pardus Sistem Temizleyici — Özel dairesel ilerleme çubuğu widget'ı

Cairo ile çizilen şık bir dairesel ilerleme göstergesi.
Disk kullanım yüzdesi veya tarama ilerlemesi göstermek için kullanılır.
"""

import math
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Graphene


class CircularProgress(Gtk.DrawingArea):
    """Özel dairesel ilerleme çubuğu."""

    def __init__(self, size=180, line_width=12):
        super().__init__()
        self._progress = 0.0  # 0.0 — 1.0
        self._target_progress = 0.0
        self._text = ""
        self._sub_text = ""
        self._size = size
        self._line_width = line_width
        self._animation_id = None
        self._color_start = (0.29, 0.56, 0.85)  # #4A90D9
        self._color_end = (0.48, 0.41, 0.93)  # #7B68EE
        self._pulse_phase = 0.0
        self._pulsing = False

        self.set_size_request(size, size)
        self.set_draw_func(self._draw)

    def set_progress(self, value, animate=True):
        """İlerleme değerini ayarla (0.0 — 1.0)."""
        self._target_progress = max(0.0, min(1.0, value))
        if animate:
            self._start_animation()
        else:
            self._progress = self._target_progress
            self.queue_draw()

    def set_text(self, text):
        """Merkez metnini ayarla."""
        self._text = text
        self.queue_draw()

    def set_sub_text(self, text):
        """Alt metnini ayarla."""
        self._sub_text = text
        self.queue_draw()

    def set_colors(self, start_rgb, end_rgb):
        """Gradient renklerini ayarla."""
        self._color_start = start_rgb
        self._color_end = end_rgb
        self.queue_draw()

    def start_pulse(self):
        """Pulse animasyonunu başlat (tarama sırasında)."""
        self._pulsing = True
        self._pulse_phase = 0.0
        self._start_pulse_animation()

    def stop_pulse(self):
        """Pulse animasyonunu durdur."""
        self._pulsing = False

    def _start_animation(self):
        """Yumuşak geçiş animasyonu başlat."""
        if self._animation_id:
            GLib.source_remove(self._animation_id)

        def animate():
            diff = self._target_progress - self._progress
            if abs(diff) < 0.002:
                self._progress = self._target_progress
                self.queue_draw()
                self._animation_id = None
                return False

            self._progress += diff * 0.08
            self.queue_draw()
            return True

        self._animation_id = GLib.timeout_add(16, animate)

    def _start_pulse_animation(self):
        """Pulse animasyonu."""
        def pulse():
            if not self._pulsing:
                return False
            self._pulse_phase += 0.03
            if self._pulse_phase > 2 * math.pi:
                self._pulse_phase -= 2 * math.pi
            self.queue_draw()
            return True

        GLib.timeout_add(16, pulse)

    def _draw(self, area, cr, width, height):
        """Cairo ile çizim."""
        cx = width / 2
        cy = height / 2
        radius = min(width, height) / 2 - self._line_width - 4

        # ─── Arka plan halkası ───
        cr.set_line_width(self._line_width)
        cr.set_source_rgba(1, 1, 1, 0.08)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()

        # ─── İlerleme halkası (gradient) ───
        progress = self._progress
        if progress > 0.001:
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * progress

            # Gradient efekti - başlangıç ve bitiş rengi arasında geçiş
            cr.set_line_width(self._line_width)
            cr.set_line_cap(1)  # ROUND

            # Gradient simülasyonu: birçok küçük parçaya böl
            segments = max(2, int(progress * 60))
            for i in range(segments):
                t = i / segments
                angle1 = start_angle + 2 * math.pi * progress * t
                angle2 = start_angle + 2 * math.pi * progress * (i + 1) / segments

                r = self._color_start[0] + (self._color_end[0] - self._color_start[0]) * t
                g = self._color_start[1] + (self._color_end[1] - self._color_start[1]) * t
                b = self._color_start[2] + (self._color_end[2] - self._color_start[2]) * t

                # Glow efekti
                glow = 0.0
                if self._pulsing:
                    glow = 0.2 * (0.5 + 0.5 * math.sin(self._pulse_phase + t * math.pi))

                cr.set_source_rgba(
                    min(1, r + glow),
                    min(1, g + glow),
                    min(1, b + glow),
                    0.9 + glow * 0.1
                )
                cr.arc(cx, cy, radius, angle1, angle2 + 0.02)
                cr.stroke()

        # ─── Pulse glow halkası ───
        if self._pulsing:
            alpha = 0.15 + 0.1 * math.sin(self._pulse_phase)
            cr.set_source_rgba(
                self._color_start[0],
                self._color_start[1],
                self._color_start[2],
                alpha
            )
            cr.set_line_width(self._line_width + 8)
            cr.arc(cx, cy, radius, 0, 2 * math.pi)
            cr.stroke()

        # ─── Merkez metni ───
        if self._text:
            cr.select_font_face("Inter", 0, 1)  # NORMAL, BOLD
            cr.set_font_size(28)
            extents = cr.text_extents(self._text)
            cr.move_to(
                cx - extents.width / 2 - extents.x_bearing,
                cy - extents.height / 2 - extents.y_bearing - (8 if self._sub_text else 0)
            )
            cr.set_source_rgba(1, 1, 1, 0.95)
            cr.show_text(self._text)

        # ─── Alt metin ───
        if self._sub_text:
            cr.select_font_face("Inter", 0, 0)  # NORMAL, NORMAL
            cr.set_font_size(12)
            extents = cr.text_extents(self._sub_text)
            cr.move_to(
                cx - extents.width / 2 - extents.x_bearing,
                cy + 18
            )
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.show_text(self._sub_text)
