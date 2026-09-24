# UPSTREAM

## 当前目标

- 版本/tag：`1.37.3`
- 上游仓库：<https://github.com/dani-garcia/vaultwarden>
- 正式发布：<https://github.com/dani-garcia/vaultwarden/releases/tag/1.37.3>
- peeled commit：`eb212e23fad88e6136723f43e5b73543fa7026d3`
- 官方模板路径：`src/static/templates`
- 本项目范围：`admin/*.hbs`、`email/*.hbs`

`upstream/1.37.3` 保存 6 个 admin 和 63 个 email 官方模板、manifest 与 SHA-256。`scripts/check_upstream_manifest.py --version 1.37.3 --source-git <vaultwarden-git>` 可进一步逐文件核对固定 commit 的 Git object。历史 `upstream/1.36.0`、`upstream/1.37.0` 继续保留并可分别校验。

## 1.37.0 → 1.37.3 范围变化

此升级包含真实模板变化，不是零译文变化：

- `admin/diagnostics.hbs`：新增 `page_data.template_overrides` 状态与详情；
- `admin/users.hbs`：操作列结构和两个 ISO 日期排序属性变化，移除旧 jQuery；
- `admin/organizations.hbs`：操作列结构变化，移除旧 jQuery；
- `email/admin_reset_password.{hbs,html.hbs}` 被 `email/admin_account_recovery.{hbs,html.hbs}` 替代；新邮件支持主密码重置、2FA 重置和邮件 2FA fallback。

版本记录：`1.37.1` 引入上述 admin/email 模板差异；`1.37.2`、`1.37.3` 的后续变更经过审计，最终以 `1.37.3` 的 69 文件树作为本发布基线。

官方完整模板还包含顶层 `404.hbs` 与 `scss/`；它们在 `1.37.0..1.37.3` 中保持不变且不属于本项目范围。Vaultwarden 会为未覆盖文件使用内置模板，因此发布包不得混入其他版本的 `404.hbs` 或 `scss/`。admin JavaScript/CSS 也由官方镜像提供。

## 动态配置边界

`CLIENT_SUPPRESS_ONBOARDING`、`SSO_SIGNUPS_ALLOWED` 以及 feature flag `pm-32413-multi-client-password-management` 的名称/说明来自 Rust 配置或 feature 文档，不是固定 Handlebars 文案。本纯模板包不维护这些键的翻译；这与既有动态设置页文案边界一致。

## 更新与验证

1. 仅从目标 tag/commit 的 Git object 导出新 `upstream/<version>` 基线。
2. 对照 name-status 清单迁移中文模板，不整目录覆盖译文。
3. 运行 `make check` 与 source-git manifest 校验。
4. 运行 `make package-check`，构建并安全审计发布归档。
5. 容器、浏览器与邮件真实路径验证作为独立运行时阶段执行。
