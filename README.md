# vaultwarden-lang-zhcn

vaultwarden 简体中文模板翻译包初版，面向 vaultwarden `1.36.0` 的 `admin` 与 `email` Handlebars 模板。

本仓库是**纯模板翻译包**，不 fork、不分发 vaultwarden 服务端源码。安装时仅将 `templates/admin` 与 `templates/email` 覆盖或挂载到 vaultwarden 对应模板目录。

## 内容

- `templates/admin/`：管理后台模板简体中文翻译。
- `templates/email/`：邮件模板简体中文翻译。
- `upstream/1.36.0/`：用于校验的官方 1.36.0 admin/email 模板基线。
- `scripts/`：本地校验与打包脚本。

## 使用

请先备份现有模板。根据你的部署方式，将本仓库的模板目录复制或挂载到 vaultwarden 使用的模板路径，例如：

```bash
cp -a templates/admin /path/to/vaultwarden/templates/
cp -a templates/email /path/to/vaultwarden/templates/
```

Docker 部署通常可通过 volume 将模板目录挂载到容器内对应模板位置；具体路径请以你的镜像/部署配置为准。

## 已知边界

vaultwarden 的管理后台并不是完整 i18n 应用。本项目只覆盖官方支持的 Handlebars 模板，因此仍可能看到少量英文：

- 设置页中大量配置项名称、说明、tooltip 来自 vaultwarden 程序内置配置文档数据，而不是 `admin/*.hbs` 模板文本。
- 管理后台部分弹窗和异步操作提示来自内置静态 JavaScript（例如 `admin_settings.js`），不能通过 `/data/templates` 覆盖。
- `SMTP`、`SSO`、`2FA`、`WebAuthn`、`FIDO2`、`Vaultwarden` 等产品/技术名默认保留英文。

如果需要翻译这些内容，需要维护 vaultwarden 源码或静态资源 fork；这不属于本纯模板包目标。

## 校验

```bash
make check
```

校验内容：

1. `upstream/1.36.0/manifest.json` 与 `checksums.json` 固定官方仓库、tag、commit、admin/email 范围、文件列表及 SHA-256，并校验 vendored upstream 文件未漂移。
2. `templates/admin`、`templates/email` 文件列表与官方 1.36.0 基线一致。
3. Handlebars token、block、partial、triple braces 与官方模板保持一致。
4. 除 `email_header.hbs`、`email_footer.hbs`、`email_footer_text.hbs` 三个 partial 外，所有 email `.hbs` / `.html.hbs` 模板均保留恰好一个 `<!---------------->` subject/body 分隔符。

也可单独运行：

```bash
make check-upstream
```

## 容器 smoke test

如果本机已有 Docker 镜像 `vaultwarden/server:1.36.0`，可运行：

```bash
make smoke
```

脚本会启动临时 vaultwarden 容器，默认监听 `127.0.0.1:8099`，只读挂载本仓库 `templates/` 到 `/data/templates`，验证 `/alive`、中文 admin 登录页，以及登录后的 `/admin`、`/admin/diagnostics`、`/admin/users/overview`、`/admin/organizations/overview`。端口和镜像可用环境变量覆盖：`SMOKE_PORT=8098 VAULTWARDEN_IMAGE=vaultwarden/server:1.36.0 make smoke`。脚本不会自动拉取镜像，缺失时返回 skip，并会自动清理容器和临时目录。

可选 SMTP debug 验证：

```bash
SMTP_SMOKE=1 make smoke
```

SMTP smoke 使用脚本内置的极简本地 SMTP debug server，默认监听 `127.0.0.1:1025`，可通过 `SMTP_SMOKE_PORT=1026` 覆盖。为避免 Docker `host-gateway`/防火墙差异，启用 SMTP smoke 时脚本会使用 Docker host networking 并设置 `ROCKET_PORT=$SMOKE_PORT`；该模式主要面向 Linux Docker 环境。普通 `make smoke` 不使用 host networking。

## 实机验证记录

初版已用 `vaultwarden/server:1.36.0` 在本机容器中挂载本项目 `templates/` 做过 smoke test：

- `/admin` 登录页可渲染中文模板。
- 登录后 `/admin`、`/admin/diagnostics`、`/admin/users/overview`、`/admin/organizations/overview` 均返回 `200 OK`。
- `/admin/test/smtp` 成功通过本机 SMTP debug server 发送测试邮件，邮件 subject/body 使用中文模板且无 template/render 错误。

## 打包

```bash
make package
```

产物输出到 `dist/`，包含 `.tar.gz` 与 `.zip`。默认包名形如：

```text
vaultwarden-lang-zhcn-admin-email-1.36.0-zh.1.tar.gz
vaultwarden-lang-zhcn-admin-email-1.36.0-zh.1.zip
```

## 翻译来源

初版主要基于官方 vaultwarden 1.36.0 模板，并迁移 wcjxixi/vaultwarden-lang-zhcn 中可对应的既有简中翻译；新增或版本差异模板按官方英文原文补译。

## 许可证

见 `LICENSE` 与 `NOTICE.md`。
