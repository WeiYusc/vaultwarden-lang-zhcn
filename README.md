# vaultwarden-lang-zhcn

适用于 Vaultwarden `1.37.3` 的 `admin` 与 `email` Handlebars 简体中文模板覆盖包。本项目不是 Vaultwarden fork，不包含服务端源码；只把 `templates/admin` 和 `templates/email` 挂载到运行时模板覆盖目录。

## 使用

请先备份已有模板。Docker 示例：

```bash
docker run ... \
  -v /path/to/vaultwarden-lang-zhcn/templates:/data/templates:ro \
  vaultwarden/server:1.37.3
```

未随包提供的顶层 `404.hbs` 与 `scss/` 仍由 Vaultwarden 内置模板回退。不要从其他版本补入这些文件。

## 1.37.3 更新

目标上游为正式 tag `1.37.3`、commit `eb212e23fad88e6136723f43e5b73543fa7026d3`：<https://github.com/dani-garcia/vaultwarden/releases/tag/1.37.3>。

从 `1.37.0` 到 `1.37.3` 不再是“译文零变化”的元数据升级：

- `diagnostics.hbs` 新增自定义模板状态和详细信息中文文案；
- `users.hbs`、`organizations.hbs` 同步 DataTables 3 所需结构，并移除旧 jQuery 引用；
- `admin_reset_password.hbs` / `.html.hbs` 被 `admin_account_recovery.hbs` / `.html.hbs` 替代；
- 新账户恢复邮件覆盖主密码重置、2FA 重置以及邮件 2FA fallback。

发布序列记录：`1.37.1` 引入本轮模板差异，`1.37.2` 与 `1.37.3` 继续纳入审核并以 `1.37.3` 作为发布基线。历史 `upstream/1.36.0`、`upstream/1.37.0` 保留用于回滚与旧版本校验。

## 已知边界

本项目仅翻译固定 Handlebars 文案。设置项名称、说明和 feature 文档由 Vaultwarden Rust 配置或内置静态资源动态提供，不能通过 `/data/templates` 覆盖。`CLIENT_SUPPRESS_ONBOARDING`、`SSO_SIGNUPS_ALLOWED` 和 feature flag `pm-32413-multi-client-password-management` 属于该边界，可能仍显示英文。管理后台内置 JavaScript 文案也不在覆盖范围。

## 校验与打包

```bash
make check
make package-check
```

`make check` 校验 `upstream/1.37.3` manifest/checksum、文件列表、Handlebars token、邮件分隔符和有限的关键结构属性。`make package-check` 构建 tar/zip 后执行安全审计，拒绝路径穿越、链接/特殊文件、重复或禁入成员、旧邮件名，并核对两个归档与源文件的成员及内容一致性。

默认产物：

```text
vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1.tar.gz
vaultwarden-lang-zhcn-admin-email-1.37.3-zh.1.zip
```

## 容器 smoke（单独运行）

如果本机已有官方镜像，可运行 `make smoke`。默认镜像是 `vaultwarden/server:1.37.3`，脚本会核对默认镜像包含预期 registry digest；设置 `VAULTWARDEN_IMAGE` 可显式覆盖。脚本不自动拉取镜像。可用 `SMOKE_PORT` 覆盖端口；`SMTP_SMOKE=1` 在 Linux Docker 下额外执行 SMTP 测试。

本次变更的运行时验证不属于本静态/发布元数据 slice，需在后续独立执行后再更新运行时验证记录。

## 翻译来源与许可

中文译文主要参考 `wcjxixi/vaultwarden-lang-zhcn`，新增内容依据官方英文模板翻译并保持 token/结构契约。详见 `UPSTREAM.md`、`TRANSLATION_STATUS.md`、`NOTICE.md` 与 `LICENSE`。
