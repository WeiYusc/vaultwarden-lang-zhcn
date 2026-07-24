#!/usr/bin/env python3
"""Build release archives containing templates and documentation."""
from pathlib import Path
import argparse
import shutil
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "vaultwarden-lang-zhcn-admin-email-1.37.0-zh.1"
INCLUDE = [
    "templates",
    "README.md",
    "LICENSE",
    "NOTICE.md",
    "UPSTREAM.md",
    "GLOSSARY.md",
    "TRANSLATION_STATUS.md",
]


def add_to_tar(tar: tarfile.TarFile, src: Path, arcbase: str) -> None:
    tar.add(src, arcname=f"{arcbase}/{src.relative_to(ROOT)}")


def add_to_zip(zipf: zipfile.ZipFile, src: Path, arcbase: str) -> None:
    if src.is_dir():
        for p in sorted(src.rglob("*")):
            if p.is_file():
                zipf.write(p, f"{arcbase}/{p.relative_to(ROOT)}")
    else:
        zipf.write(src, f"{arcbase}/{src.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--dist", default=str(ROOT / "dist"))
    args = parser.parse_args()
    dist = Path(args.dist)
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    tar_path = dist / f"{args.name}.tar.gz"
    zip_path = dist / f"{args.name}.zip"
    with tarfile.open(tar_path, "w:gz") as tar:
        for item in INCLUDE:
            add_to_tar(tar, ROOT / item, args.name)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for item in INCLUDE:
            add_to_zip(zipf, ROOT / item, args.name)
    print(tar_path)
    print(zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
