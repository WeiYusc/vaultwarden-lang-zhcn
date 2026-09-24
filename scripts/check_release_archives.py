#!/usr/bin/env python3
"""Audit Vaultwarden zh-CN release tar/zip archives for safety and exact content."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path, PurePosixPath
import stat
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1"
PUBLIC_DOCS = (
    "README.md",
    "LICENSE",
    "NOTICE.md",
    "UPSTREAM.md",
    "GLOSSARY.md",
    "TRANSLATION_STATUS.md",
)
FORBIDDEN_PARTS = {".git", ".hermes", "scripts", "upstream", "dist", "__pycache__"}
OBSOLETE_EMAILS = {"admin_reset_password.hbs", "admin_reset_password.html.hbs"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_name(raw: str, prefix: str) -> tuple[str | None, str | None]:
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != prefix:
        return None, f"unsafe path: {raw}"
    relative = PurePosixPath(*path.parts[1:])
    if not relative.parts:
        return None, None
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        return None, f"forbidden archive path: {raw}"
    if relative.parts[0] not in {"templates", *PUBLIC_DOCS}:
        return None, f"forbidden archive path: {raw}"
    if relative.parts[0] == "templates":
        if len(relative.parts) == 1 or (len(relative.parts) == 2 and relative.parts[1] in {"admin", "email"}):
            return relative.as_posix(), None
        if len(relative.parts) < 3 or relative.parts[1] not in {"admin", "email"}:
            return None, f"forbidden template path: {raw}"
        if relative.name == "404.hbs" or "scss" in relative.parts:
            return None, f"forbidden template path: {raw}"
    elif len(relative.parts) != 1:
        return None, f"forbidden archive path: {raw}"
    if relative.name in OBSOLETE_EMAILS:
        return None, f"obsolete email template: {raw}"
    return relative.as_posix(), None


def read_tar(path: Path, prefix: str) -> tuple[dict[str, bytes], list[str]]:
    files: dict[str, bytes] = {}
    errors: list[str] = []
    with tarfile.open(path, "r:*") as archive:
        names = [member.name.rstrip("/") for member in archive.getmembers()]
        for name, count in Counter(names).items():
            if count > 1:
                errors.append(f"duplicate tar member: {name}")
        for member in archive.getmembers():
            rel, error = validate_name(member.name.rstrip("/"), prefix)
            if member.isdir():
                errors.append(f"directory member is not allowed: {member.name}")
                continue
            if error:
                errors.append(error)
                continue
            if member.issym() or member.islnk():
                errors.append(f"symlink/hardlink is not allowed: {member.name}")
                continue
            if not member.isfile():
                errors.append(f"special file is not allowed: {member.name}")
                continue
            if rel is None:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                errors.append(f"could not read tar member: {member.name}")
            else:
                files[rel] = extracted.read()
    return files, errors


def read_zip(path: Path, prefix: str) -> tuple[dict[str, bytes], list[str]]:
    files: dict[str, bytes] = {}
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = [info.filename.rstrip("/") for info in archive.infolist()]
        for name, count in Counter(names).items():
            if count > 1:
                errors.append(f"duplicate zip member: {name}")
        for info in archive.infolist():
            rel, error = validate_name(info.filename.rstrip("/"), prefix)
            if error:
                errors.append(error)
                continue
            mode = info.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if file_type == stat.S_IFLNK:
                errors.append(f"symlink is not allowed: {info.filename}")
                continue
            if info.is_dir():
                continue
            if file_type not in {0, stat.S_IFREG}:
                errors.append(f"special file is not allowed: {info.filename}")
                continue
            if rel is not None:
                files[rel] = archive.read(info)
    return files, errors


def expected_files(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for subdir in ("admin", "email"):
        for path in sorted((root / "templates" / subdir).rglob("*.hbs")):
            if path.is_file():
                result[path.relative_to(root).as_posix()] = path.read_bytes()
    for name in PUBLIC_DOCS:
        path = root / name
        if path.is_file():
            result[name] = path.read_bytes()
    return result


def compare(label: str, actual: dict[str, bytes], expected: dict[str, bytes]) -> list[str]:
    errors: list[str] = []
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    for name in missing:
        errors.append(f"{label} missing expected member: {name}")
    for name in extra:
        errors.append(f"{label} extra member: {name}")
    for name in sorted(expected.keys() & actual.keys()):
        if expected[name] != actual[name]:
            errors.append(f"{label} content mismatch: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--tar", dest="tar_path", type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    tar_path = args.tar_path or root / "dist" / f"{args.name}.tar.gz"
    zip_path = args.zip_path or root / "dist" / f"{args.name}.zip"
    errors: list[str] = []
    for path in (tar_path, zip_path):
        if not path.is_file():
            errors.append(f"missing release archive: {path}")
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    tar_files, tar_errors = read_tar(tar_path, args.name)
    zip_files, zip_errors = read_zip(zip_path, args.name)
    expected = expected_files(root)
    errors.extend(tar_errors)
    errors.extend(zip_errors)
    errors.extend(compare("tar", tar_files, expected))
    errors.extend(compare("zip", zip_files, expected))
    if tar_files.keys() != zip_files.keys():
        errors.append("tar/zip member parity mismatch")
    for name in sorted(tar_files.keys() & zip_files.keys()):
        if tar_files[name] != zip_files[name]:
            errors.append(f"tar/zip content mismatch: {name}")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print(f"[OK] {len(expected)} archive members match source and tar/zip parity")
    print(f"[OK] tar.gz sha256 {digest(tar_path.read_bytes())}  {tar_path.name}")
    print(f"[OK] zip sha256 {digest(zip_path.read_bytes())}  {zip_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
