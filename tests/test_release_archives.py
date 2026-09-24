from __future__ import annotations

import io
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
import warnings
import zipfile


REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "scripts/check_release_archives.py"
NAME = "vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1"
DOCS = ("README.md", "LICENSE", "NOTICE.md", "UPSTREAM.md", "GLOSSARY.md", "TRANSLATION_STATUS.md")


class ReleaseArchiveChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "templates/admin").mkdir(parents=True)
        (self.root / "templates/email").mkdir(parents=True)
        (self.root / "templates/admin/base.hbs").write_text("admin\n", encoding="utf-8")
        (self.root / "templates/email/admin_account_recovery.hbs").write_text("text\n", encoding="utf-8")
        (self.root / "templates/email/admin_account_recovery.html.hbs").write_text("html\n", encoding="utf-8")
        for doc in DOCS:
            (self.root / doc).write_text(f"{doc}\n", encoding="utf-8")
        self.tar_path = self.root / f"{NAME}.tar.gz"
        self.zip_path = self.root / f"{NAME}.zip"
        self.write_valid_archives()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def expected_files(self) -> list[Path]:
        return sorted(
            [path for path in (self.root / "templates").rglob("*") if path.is_file()]
            + [self.root / doc for doc in DOCS]
        )

    def write_valid_archives(self) -> None:
        with tarfile.open(self.tar_path, "w:gz") as archive:
            for path in self.expected_files():
                archive.add(path, arcname=f"{NAME}/{path.relative_to(self.root)}", recursive=False)
        with zipfile.ZipFile(self.zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in self.expected_files():
                archive.write(path, f"{NAME}/{path.relative_to(self.root)}")

    def run_check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3", str(CHECKER), "--root", str(self.root),
                "--tar", str(self.tar_path), "--zip", str(self.zip_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_rejected(self, expected: str) -> None:
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout + result.stderr)

    def append_tar(self, name: str, *, kind: bytes | None = None) -> None:
        original: list[tuple[tarfile.TarInfo, bytes | None]] = []
        with tarfile.open(self.tar_path, "r:gz") as archive:
            for member in archive.getmembers():
                extracted = archive.extractfile(member) if member.isfile() else None
                original.append((member, extracted.read() if extracted else None))
        with tarfile.open(self.tar_path, "w:gz") as archive:
            for member, payload in original:
                archive.addfile(member, io.BytesIO(payload) if payload is not None else None)
            info = tarfile.TarInfo(name)
            data = b"bad\n"
            info.size = len(data)
            if kind is not None:
                info.type = kind
                info.size = 0
                info.linkname = "target"
            archive.addfile(info, None if kind is not None else io.BytesIO(data))

    def append_zip(self, name: str, *, symlink: bool = False) -> None:
        with zipfile.ZipFile(self.zip_path, "a", zipfile.ZIP_DEFLATED) as archive:
            if symlink:
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, "target")
            else:
                archive.writestr(name, "bad\n")

    def test_valid_archives_have_exact_parity(self) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("archive members", result.stdout)
        self.assertIn("sha256", result.stdout)

    def test_rejects_missing_member(self) -> None:
        with zipfile.ZipFile(self.zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in self.expected_files()[1:]:
                archive.write(path, f"{NAME}/{path.relative_to(self.root)}")
        self.assert_rejected("missing")

    def test_rejects_extra_member(self) -> None:
        self.append_zip(f"{NAME}/scripts/internal.py")
        self.assert_rejected("forbidden")

    def test_rejects_duplicate_member(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.append_zip(f"{NAME}/README.md")
        self.assert_rejected("duplicate")

    def test_rejects_traversal(self) -> None:
        self.append_zip(f"{NAME}/../escape")
        self.assert_rejected("unsafe path")

    def test_rejects_absolute_path(self) -> None:
        self.append_zip("/absolute")
        self.assert_rejected("unsafe path")

    def test_rejects_symlink(self) -> None:
        self.append_zip(f"{NAME}/templates/email/link.hbs", symlink=True)
        self.assert_rejected("symlink")

    def test_rejects_tar_directory_member(self) -> None:
        self.append_tar(f"{NAME}/templates/extra", kind=tarfile.DIRTYPE)
        self.assert_rejected("directory member")

    def test_rejects_tar_special_file(self) -> None:
        self.append_tar(f"{NAME}/templates/email/device", kind=tarfile.CHRTYPE)
        self.assert_rejected("special")

    def test_rejects_obsolete_email_name(self) -> None:
        self.append_zip(f"{NAME}/templates/email/admin_reset_password.hbs")
        self.assert_rejected("obsolete")

    def test_rejects_mismatched_member_content(self) -> None:
        with zipfile.ZipFile(self.zip_path, "a", zipfile.ZIP_DEFLATED) as archive:
            # Rebuild is needed to avoid a duplicate masking the content mismatch.
            pass
        replacement = self.root / "replacement.zip"
        with zipfile.ZipFile(replacement, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in self.expected_files():
                arcname = f"{NAME}/{path.relative_to(self.root)}"
                archive.writestr(arcname, b"changed\n" if path.name == "README.md" else path.read_bytes())
        replacement.replace(self.zip_path)
        self.assert_rejected("content mismatch")


if __name__ == "__main__":
    unittest.main()
