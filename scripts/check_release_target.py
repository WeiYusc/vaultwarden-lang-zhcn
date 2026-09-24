#!/usr/bin/env python3
"""Check that a tree has migrated all release-facing contracts to Vaultwarden 1.37.3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "1.37.3"
TARGET_COMMIT = "eb212e23fad88e6136723f43e5b73543fa7026d3"
NEW_EMAILS = ("admin_account_recovery.hbs", "admin_account_recovery.html.hbs")
OLD_EMAILS = ("admin_reset_password.hbs", "admin_reset_password.html.hbs")
DIAGNOSTIC_TOKENS = (
    "{{#if page_data.template_overrides}}",
    "{{page_data.template_overrides}}",
    "{{#unless page_data.template_overrides}}",
)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def check(root: Path) -> list[str]:
    failures: list[str] = []
    baseline = root / "upstream" / TARGET_VERSION
    manifest_path = baseline / "manifest.json"
    if not baseline.is_dir():
        failures.append("missing 1.37.3 upstream baseline: upstream/1.37.3")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            failures.append(f"invalid 1.37.3 baseline manifest: {exc}")
        else:
            actual_commit = manifest.get("upstream", {}).get("commit")
            if actual_commit != TARGET_COMMIT:
                failures.append(f"baseline commit must be {TARGET_COMMIT}, got {actual_commit!r}")

    email = root / "templates" / "email"
    for name in NEW_EMAILS:
        if not (email / name).is_file():
            failures.append(f"missing target email template: templates/email/{name}")
    for name in OLD_EMAILS:
        if (email / name).exists():
            failures.append(f"obsolete email template remains: templates/email/{name}")

    diagnostics = read(root / "templates/admin/diagnostics.hbs")
    for token in DIAGNOSTIC_TOKENS:
        if token not in diagnostics:
            failures.append(f"missing diagnostics token: {token}")

    users = read(root / "templates/admin/users.hbs")
    date_attrs = users.count('data-sort-type="date-iso"')
    if date_attrs != 2:
        failures.append(f"users.hbs must contain exactly 2 date-iso sort attributes, got {date_attrs}")

    for rel in ("templates/admin/users.hbs", "templates/admin/organizations.hbs"):
        if "jquery-4.0.0.slim.js" in read(root / rel):
            failures.append(f"obsolete jQuery reference remains in {rel}")

    smoke = read(root / "scripts/smoke_vaultwarden_container.sh")
    if "vaultwarden/server:1.37.3" not in smoke:
        failures.append("default smoke image must be vaultwarden/server:1.37.3")
    build = read(root / "scripts/build_release.py")
    if "vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1" not in build:
        failures.append("default release package must target 1.37.3-zh.1")

    for name in ("README.md", "UPSTREAM.md", "TRANSLATION_STATUS.md"):
        if TARGET_VERSION not in read(root / name):
            failures.append(f"{name} target version must mention {TARGET_VERSION}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    failures = check(args.root.resolve())
    for failure in failures:
        print(f"[FAIL] {failure}")
    if failures:
        print(f"[FAIL] release target {TARGET_VERSION}: {len(failures)} issue(s)")
        return 1
    print(f"[OK] release target {TARGET_VERSION}: all initial contracts satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
