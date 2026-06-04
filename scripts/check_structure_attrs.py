#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "1.36.0"
TEMPLATES = ROOT / "templates"


def attr_values(text: str, attr: str) -> list[str]:
    return re.findall(rf'{re.escape(attr)}="[^"]+"', text)


def main() -> int:
    errors: list[str] = []

    for upstream_file in sorted((UPSTREAM / "admin").glob("*.hbs")):
        rel = upstream_file.relative_to(UPSTREAM)
        translated_file = TEMPLATES / rel
        upstream_text = upstream_file.read_text(encoding="utf-8")
        translated_text = translated_file.read_text(encoding="utf-8")
        upstream_classes = attr_values(upstream_text, "class")
        translated_classes = attr_values(translated_text, "class")
        upstream_containers = [c for c in upstream_classes if "container-" in c]
        translated_containers = [c for c in translated_classes if "container-" in c]
        if upstream_containers != translated_containers:
            errors.append(
                f"container class mismatch: {rel}: "
                f"upstream={upstream_containers} translated={translated_containers}"
            )

    for upstream_file in sorted((UPSTREAM / "email").glob("*.html.hbs")):
        rel = upstream_file.relative_to(UPSTREAM)
        translated_file = TEMPLATES / rel
        upstream_text = upstream_file.read_text(encoding="utf-8")
        translated_text = translated_file.read_text(encoding="utf-8")
        upstream_testids = attr_values(upstream_text, "data-testid")
        translated_testids = attr_values(translated_text, "data-testid")
        if upstream_testids != translated_testids:
            errors.append(
                f"data-testid mismatch: {rel}: "
                f"upstream={upstream_testids} translated={translated_testids}"
            )

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[OK] structure attributes match upstream baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
