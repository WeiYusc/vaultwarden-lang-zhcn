# vaultwarden-lang-zhcn

vaultwarden 简体中文模板翻译包，适用于 vaultwarden `1.36.0` 的 `admin` 与 `email` Handlebars 模板。

本仓库仅提供 vaultwarden 模板文件的简体中文翻译，不是 vaultwarden 的 fork，也不包含或分发 vaultwarden 服务端源码。安装时仅将 `templates/admin` 与 `templates/email` 放入或挂载到 vaultwarden 的模板覆盖目录，不需要修改容器镜像内的源码文件。

## 内容

- `templates/admin/`：管理后台模板简体中文翻译。
- `templates/email/`：邮件模板简体中文翻译。
- `upstream/1.36.0/`：用于校验的官方 1.36.0 admin/email 模板基线。
- `scripts/`：本地校验与打包脚本。

## 使用

请先备份现有模板。本项目翻译的是 vaultwarden 官方源码中的 `src/static/templates/admin` 与 `src/static/templates/email` 模板；运行时请使用 vaultwarden 的模板覆盖目录，不要直接修改容器镜像内的源码路径。

Docker 部署通常可以将本仓库的 `templates/` 目录只读挂载到容器内 `/data/templates`，例如：

```bash
docker run ... \
  -v /path/to/vaultwarden-lang-zhcn/templates:/data/templates:ro \
  vaultwarden/server:1.36.0
```

如果使用非 Docker 部署，请将 `templates/admin` 与 `templates/email` 复制到 vaultwarden 实际读取的模板覆盖目录。具体路径仍以你的部署配置为准。

> **关于缺省模板回退：**部分 vaultwarden 安装方式的 data 目录初始并不会包含 `templates/`。这是正常现象；vaultwarden 会先尝试从 `/data/templates` 等运行时覆盖目录读取同名模板，找不到的模板继续使用程序内置的官方模板。因此，本项目只提供并覆盖 `admin/` 与 `email/` 时，未随包提供的顶层 `404.hbs` 和 `scss/` 模板仍会从 vaultwarden 内置模板加载，不会因为 `/data/templates` 目录里没有这些文件而导致 404 页面或 CSS 失效。不要为了“补齐目录”混入其他 vaultwarden 版本或其他实例的 `404.hbs`/`scss` 文件；如确需自定义它们，应使用与你当前 vaultwarden 版本完全一致的官方模板作为基线单独维护。

## 已知边界

vaultwarden 管理后台目前并非所有文本都通过 Handlebars 模板提供。本项目只覆盖官方支持通过模板覆盖的内容，因此仍可能看到少量英文：

- 设置页中大量配置项名称、说明、tooltip 来自 vaultwarden 程序内置配置文档数据，而不是 `admin/*.hbs` 模板文本。
- 管理后台部分弹窗和异步操作提示来自内置静态 JavaScript（例如 `admin_settings.js`），不能通过 `/data/templates` 覆盖。
- `SMTP`、`SSO`、`2FA`、`WebAuthn`、`FIDO2`、`Vaultwarden` 等产品/技术名默认保留英文。

如需翻译这些内容，通常需要维护 vaultwarden 源码或内置静态资源的自定义 fork；这超出了本模板翻译包的目标范围。

## 校验

```bash
make check
```

校验内容：

1. `upstream/1.36.0/manifest.json` 与 `checksums.json` 固定官方仓库、tag、commit、admin/email 范围、文件列表及 SHA-256，并校验本仓库保存的上游基线文件未漂移。
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

脚本会启动临时 vaultwarden 容器，默认监听 `127.0.0.1:8099`，并将本仓库 `templates/` 只读挂载到 `/data/templates`。

验证范围包括 `/alive`、中文 admin 登录页，以及登录后的 `/admin`、`/admin/diagnostics`、`/admin/users/overview`、`/admin/organizations/overview`。端口和镜像可用环境变量覆盖：`SMOKE_PORT=8098 VAULTWARDEN_IMAGE=vaultwarden/server:1.36.0 make smoke`。脚本不会自动拉取镜像，缺失时返回 skip，并会自动清理容器和临时目录。

可选 SMTP debug 验证：

```bash
SMTP_SMOKE=1 make smoke
```

SMTP smoke 使用脚本内置的极简本地 SMTP 调试服务器，默认监听 `127.0.0.1:1025`，可通过 `SMTP_SMOKE_PORT=1026` 覆盖。为避免 Docker `host-gateway`/防火墙差异，启用 SMTP smoke 时脚本会使用 Docker host networking 并设置 `ROCKET_PORT=$SMOKE_PORT`；该模式主要面向 Linux Docker 环境。普通 `make smoke` 不使用 host networking。

## 本地容器验证记录

当前版本已使用 `vaultwarden/server:1.36.0` 在本地容器中挂载本项目 `templates/` 完成以下 smoke test：

- `/admin` 登录页可渲染中文模板。
- 登录后 `/admin`、`/admin/diagnostics`、`/admin/users/overview`、`/admin/organizations/overview` 均返回 `200 OK`。
- `/admin/test/smtp` 成功通过本地 SMTP 调试服务器发送测试邮件，邮件 subject/body 使用中文模板且无 template/render 错误。

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

当前版本基于 vaultwarden 官方仓库 `1.36.0` 模板制作：<https://github.com/dani-garcia/vaultwarden>。

简体中文译文主要参考 `wcjxixi/vaultwarden-lang-zhcn`，并在与当前模板结构可对应时复用既有译文：<https://github.com/wcjxixi/vaultwarden-lang-zhcn>。

新增模板和版本差异内容根据官方英文原文补译。

## 许可证

见 `LICENSE` 与 `NOTICE.md`。
