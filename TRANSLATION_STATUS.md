# TRANSLATION_STATUS

目标版本：vaultwarden `1.37.0`

## 摘要

| 类别 | 文件数 | 状态 |
| --- | ---: | --- |
| admin | 6 | 已建立简体中文翻译，基于 `wcjxixi/vaultwarden-lang-zhcn` 的 `admin - v1.35.4` 参考翻译迁移，并与 1.37.0 token 校验对齐。1.36.0 到 1.37.0 的官方 admin 模板内容未变化。 |
| email | 63 | 已建立简体中文翻译，基于 `wcjxixi/vaultwarden-lang-zhcn` 的 `email - v1.32.4` 参考翻译迁移；此前缺失模板已按官方英文原文补译并完成重点复核。1.36.0 到 1.37.0 的官方 email 模板内容未变化。 |

## 校验状态

- 文件列表：与 `upstream/1.37.0/admin`、`upstream/1.37.0/email` 对齐。
- Handlebars token：通过 `scripts/check_tokens.py` 校验，要求 token 序列保持一致并保留 triple braces。
- 邮件分隔符：普通文本邮件模板保留恰好一个 `<!---------------->`；仅 `email_header.hbs`、`email_footer.hbs`、`email_footer_text.hbs` 三个 partial 例外；HTML 邮件模板同样必须保留 delimiter。
- 已确认 `1.37.0` 新增的 3 项配置文档来自 `src/config.rs` 动态数据，不属于本项目可覆盖的模板固定文案。

## 补译模板复核

以下邮件模板在参考翻译版本中不存在，已依据 vaultwarden 官方英文原文补译；其内容在 `1.36.0` 与 `1.37.0` 间未发生变化。复核范围包括文本版与 HTML 版的语义、术语、Handlebars token、HTML 链接和邮件分隔符。

| 模板 | 状态 | 审校备注 |
| --- | --- | --- |
| `change_email_existing.hbs` / `change_email_existing.html.hbs` | 已审校 | 保留 `acting_address` / `existing_address` 语义；说明已有账户使用目标邮箱，并提示非本人操作时联系管理员。 |
| `change_email_invited.hbs` / `change_email_invited.html.hbs` | 已审校 | 保留删除账户恢复链接 `{{url}}/#/recover-delete`；text/html 版本均说明需重新发送邀请。 |
| `protected_action.hbs` / `protected_action.html.hbs` | 已审校 | “protected action” 统一译为“受保护操作”；验证码 `{{token}}` 位置与 HTML 加粗结构保持一致。 |
| `register_verify_email.hbs` / `register_verify_email.html.hbs` | 已审校 | 保留 triple braces `{{{url}}}`；按钮文案与文本链接语义一致。 |
| `sso_change_email.hbs` / `sso_change_email.html.hbs` | 已审校 | “SSO Provider” 统一译为“SSO 提供商”；HTML 版本保留账户设置链接 `{{url}}/`。 |

## 维护说明

- 升级 vaultwarden 上游版本时，应先更新 `upstream/<version>/manifest.json` 与 `checksums.json`，再迁移模板并复核新增或变更内容。
- 更新后建议运行 `make check`，确认文件列表、Handlebars token、邮件分隔符和关键结构属性仍与上游模板匹配。
