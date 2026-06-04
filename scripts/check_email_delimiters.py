#!/usr/bin/env python3
"""Check email templates keep exactly one subject/body delimiter.

Vaultwarden parses both text (``name.hbs``) and HTML (``name.html.hbs``)
templates with the same ``<!---------------->`` subject/body delimiter. The
three shared partials are the only email templates that intentionally omit it.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EMAIL = ROOT / "templates" / "email"
DELIMITER = "<!---------------->"
PARTIALS = {"email_header.hbs", "email_footer.hbs", "email_footer_text.hbs"}

ok = True
for path in sorted(EMAIL.glob("*.hbs")):
    if path.name in PARTIALS:
        print(f"[SKIP] delimiter: {path.name}")
        continue
    text = path.read_text(encoding="utf-8")
    count = text.count(DELIMITER)
    parts = text.split(DELIMITER)
    if count != 1:
        ok = False
        print(f"[FAIL] delimiter count for {path.name}: expected 1, got {count}")
    elif not parts[0].strip():
        ok = False
        print(f"[FAIL] empty email subject before delimiter: {path.name}")
    elif not parts[1].strip():
        ok = False
        print(f"[FAIL] empty email body after delimiter: {path.name}")
    else:
        print(f"[OK] delimiter: {path.name}")

sys.exit(0 if ok else 1)
