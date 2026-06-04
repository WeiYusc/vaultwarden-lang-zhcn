#!/usr/bin/env python3
"""Check translated admin/email file lists match the vendored upstream baseline."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "1.36.0"
TEMPLATES = ROOT / "templates"
SUBDIRS = ("admin", "email")

ok = True
for sub in SUBDIRS:
    upstream_files = sorted(p.relative_to(UPSTREAM / sub) for p in (UPSTREAM / sub).rglob("*.hbs"))
    translated_files = sorted(p.relative_to(TEMPLATES / sub) for p in (TEMPLATES / sub).rglob("*.hbs"))
    missing = sorted(set(upstream_files) - set(translated_files))
    extra = sorted(set(translated_files) - set(upstream_files))
    if missing or extra:
        ok = False
        print(f"[FAIL] {sub} file list mismatch")
        if missing:
            print("  Missing:")
            for item in missing:
                print(f"    - {item}")
        if extra:
            print("  Extra:")
            for item in extra:
                print(f"    - {item}")
    else:
        print(f"[OK] {sub}: {len(translated_files)} files")

sys.exit(0 if ok else 1)
