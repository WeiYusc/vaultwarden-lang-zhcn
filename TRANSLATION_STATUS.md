# TRANSLATION_STATUS

目标版本：Vaultwarden `1.37.3`

## 摘要

| 类别 | 文件数 | 状态 |
| --- | ---: | --- |
| admin | 6 | 与 `upstream/1.37.3/admin` 对齐；3 个模板迁移了 1.37.3 结构，其中 diagnostics 新增中文文案。 |
| email | 63 | 与 `upstream/1.37.3/email` 对齐；账户恢复邮件文本/HTML 对已翻译，旧管理员重置密码邮件对已删除。 |

## 本轮变化

- `diagnostics.hbs`：翻译“使用自定义模板”、是/否、详细信息及说明，并保留 `page_data.template_overrides` 条件块。
- `users.hbs`：保留两个 `data-sort-type="date-iso"`，同步操作列样式，删除旧 jQuery 引用。
- `organizations.hbs`：同步操作列样式，删除旧 jQuery 引用。
- `admin_reset_password.hbs` / `.html.hbs` 已由 `admin_account_recovery.hbs` / `.html.hbs` 替代。新邮件覆盖主密码重置、2FA 重置、两者同时重置和邮件 2FA fallback，并保留非本人操作安全提示。
- 除明确处置的 7 个路径名外，其余 64 个中文模板相对 `47c0174c7ad80c6d62c3c7d40be9c62017ec1b03` 逐字节不变。

版本审计记录：`1.37.0` 的 admin/email 与 `1.36.0` 相同；`1.37.1` 引入本轮模板变化；`1.37.2` 和 `1.37.3` 的后续状态已纳入目标审计，当前固定到 `1.37.3` commit `eb212e23fad88e6136723f43e5b73543fa7026d3`。

## 校验状态

- 文件列表：6 admin、63 email，与 `upstream/1.37.3` 一致。
- Handlebars token/block/partial/triple braces：与官方基线序列一致。
- 邮件分隔符：除三个 partial 外，每个邮件模板恰好一个 `<!---------------->`。
- 结构校验：有限覆盖 admin `container-*` class 与 HTML email `data-testid`；本轮新增的日期属性、jQuery 缺失、diagnostics 条件和账户恢复文件替换由 release-target 与迁移测试明确覆盖。
- 归档：tar/zip 必须与源文件精确一致并通过路径、类型、重复成员、禁入内容和旧文件名安全审计。

## 纯模板边界

`CLIENT_SUPPRESS_ONBOARDING`、`SSO_SIGNUPS_ALLOWED` 和 `pm-32413-multi-client-password-management` 来自动态 Rust 配置/feature 文档，不在固定 Handlebars 翻译范围。`404.hbs`、`scss/` 及 admin 内置 JavaScript/CSS 同样不由本包覆盖。

## 历史补译

此前补译并持续校验的邮件包括 `change_email_existing*`、`change_email_invited*`、`protected_action*`、`register_verify_email*` 与 `sso_change_email*`。历史 `upstream/1.36.0`、`upstream/1.37.0` 基线保留用于回滚验证。
