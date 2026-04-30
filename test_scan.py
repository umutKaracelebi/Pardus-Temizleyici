#!/usr/bin/env python3
"""Test script — tüm modülleri import eder ve tarama yapar."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Modül Import Testleri ===")

try:
    from core.rules import RuleEngine, CLEANUP_RULES
    print(f"  ✅ rules.py — {len(CLEANUP_RULES)} kural yüklendi")
except Exception as e:
    print(f"  ❌ rules.py — {e}")
    sys.exit(1)

try:
    from core.scanner import Scanner
    print("  ✅ scanner.py")
except Exception as e:
    print(f"  ❌ scanner.py — {e}")
    sys.exit(1)

try:
    from core.cleaner import Cleaner
    print("  ✅ cleaner.py")
except Exception as e:
    print(f"  ❌ cleaner.py — {e}")
    sys.exit(1)

try:
    from utils.formatter import format_size
    print("  ✅ formatter.py")
except Exception as e:
    print(f"  ❌ formatter.py — {e}")
    sys.exit(1)

print("\n=== Tarama Testi ===")
s = Scanner()
results = s.scan_all()

total = 0
for cat_id, r in results.items():
    total += r.total_size
    count = len(r.files) if r.files else 0
    print(f"  {format_size(r.total_size):>10}  {cat_id} ({count} öğe)")

print(f"\n  TOPLAM: {format_size(total)}")
print("\n=== Tüm testler başarılı ===")
