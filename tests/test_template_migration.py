from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "1.37.3"
TEMPLATES = ROOT / "templates"
TOKEN_RE = re.compile(r"\{\{\{?[^{}]*?\}?\}\}")
TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)\b[^>]*>")


def tokens(path: Path) -> list[tuple[str, str]]:
    result = []
    for match in TOKEN_RE.finditer(path.read_text(encoding="utf-8")):
        token = match.group(0)
        triple = token.startswith("{{{") and token.endswith("}}}")
        inner = token[3:-3] if triple else token[2:-2]
        result.append(("triple" if triple else "double", " ".join(inner.strip().split())))
    return result


def html_tags(path: Path) -> list[tuple[str, str]]:
    return TAG_RE.findall(path.read_text(encoding="utf-8"))


class TargetTemplateMigration(unittest.TestCase):
    def test_diagnostics_target_delta_is_present_and_structurally_exact(self) -> None:
        translated = (TEMPLATES / "admin/diagnostics.hbs").read_text(encoding="utf-8")
        upstream = (UPSTREAM / "admin/diagnostics.hbs").read_text(encoding="utf-8")
        block = """                    <dt class="col-sm-5">使用自定义模板</dt>
                    <dd class="col-sm-7">
                    {{#if page_data.template_overrides}}
                        <span class="d-inline"><b>是</b></span>
                        <span class="badge bg-info text-dark abbr-badge" title="正在使用自定义模板文件。&#013;&#010;{{page_data.template_overrides}}">详细信息</span>
                    {{/if}}
                    {{#unless page_data.template_overrides}}
                        <span class="d-block"><b>否</b></span>
                    {{/unless}}
                    </dd>
"""
        self.assertIn(block, translated)
        self.assertEqual(tokens(TEMPLATES / "admin/diagnostics.hbs"), tokens(UPSTREAM / "admin/diagnostics.hbs"))
        self.assertEqual(html_tags(TEMPLATES / "admin/diagnostics.hbs"), html_tags(UPSTREAM / "admin/diagnostics.hbs"))

    def test_users_has_only_the_required_target_structural_delta(self) -> None:
        text = (TEMPLATES / "admin/users.hbs").read_text(encoding="utf-8")
        self.assertIn('<span class="d-block text-break text-wrap">{{sso_identifier}}</span>', text)
        self.assertIn('<th class="vw-actions text-end">操作</th>', text)
        self.assertIn('<span class="d-block" data-sort-type="date-iso">{{created_at}}</span>', text)
        self.assertIn('<span class="d-block" data-sort-type="date-iso">{{last_active}}</span>', text)
        self.assertEqual(text.count('data-sort-type="date-iso"'), 2)
        self.assertNotIn("jquery-4.0.0.slim.js", text)
        self.assertEqual(tokens(TEMPLATES / "admin/users.hbs"), tokens(UPSTREAM / "admin/users.hbs"))

    def test_organizations_has_only_the_required_target_structural_delta(self) -> None:
        text = (TEMPLATES / "admin/organizations.hbs").read_text(encoding="utf-8")
        self.assertIn('<th class="vw-actions text-end">操作</th>', text)
        self.assertNotIn("jquery-4.0.0.slim.js", text)
        self.assertEqual(tokens(TEMPLATES / "admin/organizations.hbs"), tokens(UPSTREAM / "admin/organizations.hbs"))

    def test_account_recovery_pair_matches_target_control_and_html_structure(self) -> None:
        old = {
            TEMPLATES / "email/admin_reset_password.hbs",
            TEMPLATES / "email/admin_reset_password.html.hbs",
        }
        new = {
            TEMPLATES / "email/admin_account_recovery.hbs",
            TEMPLATES / "email/admin_account_recovery.html.hbs",
        }
        self.assertTrue(all(not path.exists() for path in old))
        self.assertTrue(all(path.is_file() for path in new))
        expected_phrases = (
            "来自 {{org_name}} 组织的管理员账户恢复",
            "{{user_name}} 的主密码已被更改。",
            "您的两步验证方式已被重置。",
            "已启用邮件两步验证作为后备方式。",
            "如果您没有发起此请求，请立即联系您的管理员。",
        )
        for path in sorted(new):
            text = path.read_text(encoding="utf-8")
            visible_text = re.sub(r"<[^>]+>", "", text)
            for phrase in expected_phrases:
                self.assertIn(phrase, visible_text, path.name)
            upstream = UPSTREAM / "email" / path.name
            self.assertEqual(tokens(path), tokens(upstream), path.name)
            self.assertEqual(html_tags(path), html_tags(upstream), path.name)
            self.assertEqual(text.count("<!---------------->"), 1, path.name)


if __name__ == "__main__":
    unittest.main()
