from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "scripts/check_upstream_manifest.py"
SOURCE_GIT = Path("/www/temp/hermes/project/vaultwarden-upstream-audit")
VERSION = "1.37.3"
COMMIT = "eb212e23fad88e6136723f43e5b73543fa7026d3"
TEMPLATES_PATH = "src/static/templates"


class UpstreamManifestChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = REPO / "upstream/1.37.0"
        target = self.root / "upstream" / VERSION
        shutil.copytree(source, target)
        manifest_path = target / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["upstream"]["tag"] = VERSION
        manifest["upstream"]["commit"] = COMMIT
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_check(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(CHECKER), "--root", str(self.root), "--version", VERSION, *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def mutate_manifest(self, callback) -> None:
        path = self.root / "upstream" / VERSION / "manifest.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        callback(doc)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def assert_manifest_failure(self, expected: str) -> None:
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout + result.stderr)

    def test_rejects_wrong_schema(self) -> None:
        self.mutate_manifest(lambda doc: doc.__setitem__("schema_version", 999))
        self.assert_manifest_failure("schema_version mismatch")

    def test_default_version_is_current_target(self) -> None:
        result = subprocess.run(
            ["python3", str(CHECKER), "--root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("upstream/1.37.3", result.stdout)

    def test_rejects_wrong_templates_path(self) -> None:
        self.mutate_manifest(lambda doc: doc["upstream"].__setitem__("templates_path", "wrong"))
        self.assert_manifest_failure("templates_path mismatch")

    def test_rejects_wrong_commit(self) -> None:
        self.mutate_manifest(lambda doc: doc["upstream"].__setitem__("commit", "wrong"))
        self.assert_manifest_failure("upstream.commit mismatch")

    def test_rejects_vendored_content_mutation(self) -> None:
        path = self.root / "upstream" / VERSION / "admin/base.hbs"
        path.write_bytes(path.read_bytes() + b"mutation\n")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("sha256 mismatch for admin/base.hbs", result.stdout)

    def test_source_git_rejects_content_not_from_commit(self) -> None:
        result = self.run_check("--source-git", str(SOURCE_GIT))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source content mismatch", result.stdout)

    def test_source_git_rejects_missing_or_extra_source_paths(self) -> None:
        self.mutate_manifest(lambda doc: doc["files"].pop())
        result = self.run_check("--source-git", str(SOURCE_GIT))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source file set mismatch", result.stdout)


if __name__ == "__main__":
    unittest.main()
