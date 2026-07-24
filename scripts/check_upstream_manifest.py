#!/usr/bin/env python3
"""Validate vendored upstream templates against manifest.json and checksums.json."""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "1.37.0"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_REPO = "https://github.com/dani-garcia/vaultwarden"
EXPECTED_TEMPLATES_PATH = "src/static/templates"
EXPECTED_COMMITS = {
    "1.36.0": "f21a3adae2fbb8582b60b121783c597fe6895ff4",
    "1.37.0": "46ae59eaf444f0ae0a799070cf2bd6c415284a51",
}
EXPECTED_SCOPE = ["admin", "email"]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"[FAIL] missing {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[FAIL] invalid JSON in {path.relative_to(ROOT)}: {exc}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    args = parser.parse_args()

    upstream_dir = ROOT / "upstream" / args.version
    manifest_path = upstream_dir / "manifest.json"
    checksums_path = upstream_dir / "checksums.json"
    manifest = load_json(manifest_path)
    checksums_doc = load_json(checksums_path)

    ok = True

    def fail(msg: str) -> None:
        nonlocal ok
        ok = False
        print(f"[FAIL] {msg}")

    upstream = manifest.get("upstream", {})
    if manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        fail(f"manifest schema_version mismatch: {manifest.get('schema_version')!r}")
    if upstream.get("repo") != EXPECTED_REPO:
        fail(f"manifest upstream.repo mismatch: {upstream.get('repo')!r}")
    if upstream.get("tag") != args.version:
        fail(f"manifest upstream.tag mismatch: {upstream.get('tag')!r}")
    expected_commit = EXPECTED_COMMITS.get(args.version)
    if expected_commit is None:
        fail(f"unsupported version: {args.version!r}")
    elif upstream.get("commit") != expected_commit:
        fail(f"manifest upstream.commit mismatch: {upstream.get('commit')!r}")
    if upstream.get("templates_path") != EXPECTED_TEMPLATES_PATH:
        fail(f"manifest upstream.templates_path mismatch: {upstream.get('templates_path')!r}")
    if manifest.get("scope") != EXPECTED_SCOPE:
        fail(f"manifest scope mismatch: {manifest.get('scope')!r}")
    if manifest.get("checksum_algorithm") != "sha256":
        fail(f"manifest checksum_algorithm mismatch: {manifest.get('checksum_algorithm')!r}")
    if manifest.get("checksum_file") != "checksums.json":
        fail(f"manifest checksum_file mismatch: {manifest.get('checksum_file')!r}")

    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list) or not all(isinstance(x, str) for x in manifest_files):
        fail("manifest files must be a list of strings")
        manifest_files = []
    if manifest_files != sorted(manifest_files):
        fail("manifest files must be sorted")
    if len(manifest_files) != len(set(manifest_files)):
        fail("manifest files contains duplicates")
    if manifest.get("file_count") != len(manifest_files):
        fail(f"manifest file_count mismatch: {manifest.get('file_count')!r} != {len(manifest_files)}")

    actual_files = []
    for sub in EXPECTED_SCOPE:
        actual_files.extend(p.relative_to(upstream_dir).as_posix() for p in sorted((upstream_dir / sub).rglob("*.hbs")))
    actual_files = sorted(actual_files)

    missing_from_manifest = sorted(set(actual_files) - set(manifest_files))
    extra_in_manifest = sorted(set(manifest_files) - set(actual_files))
    if missing_from_manifest:
        fail("files missing from manifest: " + ", ".join(missing_from_manifest))
    if extra_in_manifest:
        fail("manifest references missing files: " + ", ".join(extra_in_manifest))

    checksums = checksums_doc.get("sha256")
    if not isinstance(checksums, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in checksums.items()):
        fail("checksums.json must contain object sha256 mapping file paths to hex digests")
        checksums = {}

    missing_checksums = sorted(set(manifest_files) - set(checksums))
    extra_checksums = sorted(set(checksums) - set(manifest_files))
    if missing_checksums:
        fail("checksums missing entries: " + ", ".join(missing_checksums))
    if extra_checksums:
        fail("checksums contain extra entries: " + ", ".join(extra_checksums))

    for rel in manifest_files:
        if rel.startswith("/") or ".." in Path(rel).parts:
            fail(f"unsafe manifest path: {rel}")
            continue
        path = upstream_dir / rel
        if not path.is_file():
            continue
        expected = checksums.get(rel)
        actual = sha256(path)
        if expected != actual:
            fail(f"sha256 mismatch for {rel}: expected {expected}, actual {actual}")

    if ok:
        print(f"[OK] upstream/{args.version}: {len(actual_files)} files match manifest and sha256 checksums")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
