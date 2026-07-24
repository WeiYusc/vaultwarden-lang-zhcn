#!/usr/bin/env python3
"""Check Handlebars tokens/blocks/partials are preserved against upstream."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "1.37.0"
TEMPLATES = ROOT / "templates"
SUBDIRS = ("admin", "email")

# Captures {{...}} and {{{...}}}; keeps delimiter shape to protect triple braces.
TOKEN_RE = re.compile(r"\{\{\{?[^{}]*?\}?\}\}")

# Some translated reference files may normalize whitespace inside tokens. Canonicalize internal
# whitespace while preserving double vs triple braces and the helper/partial/control text.
def tokens(text: str):
    out = []
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        triple = tok.startswith("{{{") and tok.endswith("}}}")
        inner = tok[3:-3] if triple else tok[2:-2]
        inner = " ".join(inner.strip().split())
        out.append(("triple" if triple else "double", inner))
    return out

ok = True
for sub in SUBDIRS:
    for src in sorted((UPSTREAM / sub).rglob("*.hbs")):
        rel = src.relative_to(UPSTREAM / sub)
        dst = TEMPLATES / sub / rel
        if not dst.exists():
            continue
        a = tokens(src.read_text(encoding="utf-8"))
        b = tokens(dst.read_text(encoding="utf-8"))
        if a != b:
            ok = False
            print(f"[FAIL] token sequence mismatch: {sub}/{rel}")
            if sorted(a) != sorted(b):
                missing = list(a)
                for tok in b:
                    if tok in missing:
                        missing.remove(tok)
                extra = list(b)
                for tok in a:
                    if tok in extra:
                        extra.remove(tok)
                if missing:
                    print("  Missing tokens:")
                    for tok in missing:
                        print(f"    - {tok}")
                if extra:
                    print("  Extra tokens:")
                    for tok in extra:
                        print(f"    - {tok}")
            else:
                print("  Same token multiset, but order differs.")
        else:
            print(f"[OK] tokens: {sub}/{rel}")

sys.exit(0 if ok else 1)
