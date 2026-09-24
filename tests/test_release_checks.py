from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "scripts" / "check_release_target.py"
UNCHANGED_CHECKER = REPO / "scripts" / "check_unchanged_translations.py"
TARGET_COMMIT = "eb212e23fad88e6136723f43e5b73543fa7026d3"


class BaselineSelectionChecks(unittest.TestCase):
    def test_release_checkers_use_1373_baseline(self) -> None:
        for name in ("check_file_list.py", "check_tokens.py", "check_structure_attrs.py"):
            source = (REPO / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn('"1.37.3"', source, name)
            self.assertNotIn('"1.37.0"', source, name)


class ReleaseWiringChecks(unittest.TestCase):
    def test_package_smoke_make_and_ci_target_1373(self) -> None:
        build = (REPO / "scripts/build_release.py").read_text(encoding="utf-8")
        smoke = (REPO / "scripts/smoke_vaultwarden_container.sh").read_text(encoding="utf-8")
        makefile = (REPO / "Makefile").read_text(encoding="utf-8")
        ci = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1", build)
        self.assertIn("vaultwarden/server:1.37.3", smoke)
        self.assertIn("sha256:1587c45feaa479f1f5e8af3b00eded36bff77bcf1880cf8dbf0541706dd470e0", smoke)
        self.assertIn("package-check:", makefile)
        self.assertIn("scripts/check_release_archives.py", makefile)
        self.assertIn("scripts/check_release_target.py", makefile)
        self.assertIn("scripts/check_unchanged_translations.py", makefile)
        self.assertIn("test:", makefile)
        self.assertIn("unittest discover", makefile)
        self.assertIn("make test", ci)
        self.assertIn("make package-check", ci)


class ReleaseDocumentationChecks(unittest.TestCase):
    def test_docs_record_release_changes_and_dynamic_boundary(self) -> None:
        combined = "\n".join(
            (REPO / name).read_text(encoding="utf-8")
            for name in ("README.md", "UPSTREAM.md", "TRANSLATION_STATUS.md")
        )
        for expected in (
            "1.37.1", "1.37.2", "1.37.3", TARGET_COMMIT,
            "admin_account_recovery", "admin_reset_password",
            "CLIENT_SUPPRESS_ONBOARDING", "SSO_SIGNUPS_ALLOWED",
            "pm-32413-multi-client-password-management",
        ):
            self.assertIn(expected, combined)
        notice = (REPO / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("1.37.3", notice)


class ReleaseTargetChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "upstream/1.37.3").mkdir(parents=True)
        (self.root / "templates/admin").mkdir(parents=True)
        (self.root / "templates/email").mkdir(parents=True)
        (self.root / "scripts").mkdir()
        (self.root / "upstream/1.37.3/manifest.json").write_text(
            json.dumps({"upstream": {"commit": TARGET_COMMIT}}), encoding="utf-8"
        )
        (self.root / "templates/admin/diagnostics.hbs").write_text(
            "{{#if page_data.template_overrides}}\n{{page_data.template_overrides}}\n"
            "{{#unless page_data.template_overrides}}\n",
            encoding="utf-8",
        )
        (self.root / "templates/admin/users.hbs").write_text(
            '<span data-sort-type="date-iso">{{created_at}}</span>\n'
            '<span data-sort-type="date-iso">{{last_active}}</span>\n',
            encoding="utf-8",
        )
        (self.root / "templates/admin/organizations.hbs").write_text("DataTable\n", encoding="utf-8")
        for name in ("admin_account_recovery.hbs", "admin_account_recovery.html.hbs"):
            (self.root / "templates/email" / name).write_text("new\n", encoding="utf-8")
        (self.root / "scripts/smoke_vaultwarden_container.sh").write_text(
            'IMAGE="${VAULTWARDEN_IMAGE:-vaultwarden/server:1.37.3}"\n', encoding="utf-8"
        )
        (self.root / "scripts/build_release.py").write_text(
            'DEFAULT_NAME = "vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1"\n', encoding="utf-8"
        )
        for name in ("README.md", "UPSTREAM.md", "TRANSLATION_STATUS.md"):
            (self.root / name).write_text("Current target: 1.37.3\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(CHECKER), "--root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_failure(self, expected: str) -> None:
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout + result.stderr)

    def test_complete_target_fixture_passes(self) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("release target 1.37.3", result.stdout)

    def test_missing_baseline_fails(self) -> None:
        shutil.rmtree(self.root / "upstream/1.37.3")
        self.assert_failure("missing 1.37.3 upstream baseline")

    def test_wrong_baseline_commit_fails(self) -> None:
        manifest = self.root / "upstream/1.37.3/manifest.json"
        manifest.write_text(json.dumps({"upstream": {"commit": "wrong"}}), encoding="utf-8")
        self.assert_failure("baseline commit")

    def test_new_email_missing_fails(self) -> None:
        (self.root / "templates/email/admin_account_recovery.hbs").unlink()
        self.assert_failure("missing target email template")

    def test_old_email_remaining_fails(self) -> None:
        (self.root / "templates/email/admin_reset_password.hbs").write_text("old\n", encoding="utf-8")
        self.assert_failure("obsolete email template remains")

    def test_diagnostics_tokens_missing_fails(self) -> None:
        (self.root / "templates/admin/diagnostics.hbs").write_text("old\n", encoding="utf-8")
        self.assert_failure("diagnostics token")

    def test_users_requires_exactly_two_date_attributes(self) -> None:
        users = self.root / "templates/admin/users.hbs"
        users.write_text(users.read_text(encoding="utf-8") + '<i data-sort-type="date-iso"></i>\n', encoding="utf-8")
        self.assert_failure("exactly 2")

    def test_jquery_reference_fails(self) -> None:
        users = self.root / "templates/admin/users.hbs"
        users.write_text(users.read_text(encoding="utf-8") + "jquery-4.0.0.slim.js\n", encoding="utf-8")
        self.assert_failure("obsolete jQuery")

    def test_wrong_default_image_fails(self) -> None:
        smoke = self.root / "scripts/smoke_vaultwarden_container.sh"
        smoke.write_text(smoke.read_text().replace("1.37.3", "1.37.0"), encoding="utf-8")
        self.assert_failure("default smoke image")

    def test_wrong_default_package_name_fails(self) -> None:
        build = self.root / "scripts/build_release.py"
        build.write_text(build.read_text().replace("1.37.3-zh.1", "1.37.0-zh.1"), encoding="utf-8")
        self.assert_failure("default release package")

    def test_stale_document_target_fails(self) -> None:
        (self.root / "README.md").write_text("Current target: 1.37.0\n", encoding="utf-8")
        self.assert_failure("README.md target version")


class UnchangedTranslationChecks(unittest.TestCase):
    def run_check(self, worktree: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(UNCHANGED_CHECKER), "--root", str(worktree)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_repository_has_exactly_64_unchanged_keep_templates(self) -> None:
        result = self.run_check(REPO)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("64 unchanged translation files", result.stdout)

    def test_mutating_keep_template_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "repo"
            subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(clone)], check=True)
            target = clone / "templates/admin/base.hbs"
            target.write_bytes(target.read_bytes() + b"\nmutation\n")
            result = self.run_check(clone)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("changed KEEP translation: templates/admin/base.hbs", result.stdout)


if __name__ == "__main__":
    unittest.main()
