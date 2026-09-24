#!/usr/bin/env python3
"""Prove release-unaffected Chinese templates equal immutable BASE_COMMIT Git blobs."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "47c0174c7ad80c6d62c3c7d40be9c62017ec1b03"
EXCLUDED = {
    "templates/admin/diagnostics.hbs",
    "templates/admin/organizations.hbs",
    "templates/admin/users.hbs",
    "templates/email/admin_account_recovery.hbs",
    "templates/email/admin_account_recovery.html.hbs",
    "templates/email/admin_reset_password.hbs",
    "templates/email/admin_reset_password.html.hbs",
}
EXPECTED_KEEP_COUNT = 64


def git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()

    listing = git(root, "ls-tree", "-r", "--name-only", BASE_COMMIT, "--", "templates/admin", "templates/email")
    if listing.returncode:
        print(f"[FAIL] cannot read BASE_COMMIT {BASE_COMMIT}: {listing.stderr.decode(errors='replace').strip()}")
        return 1
    baseline_paths = sorted(listing.stdout.decode().splitlines())
    keep_paths = [path for path in baseline_paths if path not in EXCLUDED]
    ok = True
    if len(keep_paths) != EXPECTED_KEEP_COUNT:
        print(f"[FAIL] expected {EXPECTED_KEEP_COUNT} KEEP paths, got {len(keep_paths)}")
        ok = False

    for rel in keep_paths:
        baseline = git(root, "show", f"{BASE_COMMIT}:{rel}")
        if baseline.returncode:
            print(f"[FAIL] cannot read baseline Git object: {rel}")
            ok = False
            continue
        path = root / rel
        if not path.is_file():
            print(f"[FAIL] missing KEEP translation: {rel}")
            ok = False
        elif path.read_bytes() != baseline.stdout:
            print(f"[FAIL] changed KEEP translation: {rel}")
            ok = False

    if not ok:
        return 1
    print(f"[OK] {len(keep_paths)} unchanged translation files match {BASE_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
