#!/usr/bin/env python3
"""
Pardus Sistem Temizleyici — Giriş Noktası

Modern, güvenli ve kullanıcı dostu Linux sistem temizleme aracı.
"""

import sys
import os

# Modül yolunu ayarla
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

from application import Application


def main():
    app = Application()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
