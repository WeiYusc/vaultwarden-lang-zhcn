# UPSTREAM

## vaultwarden

- 目标版本：`1.37.0`
- 上游仓库：`https://github.com/dani-garcia/vaultwarden`
- 上游提交：`46ae59eaf444f0ae0a799070cf2bd6c415284a51`
- 官方模板相对路径：`src/static/templates`
- 纳入范围：
  - `src/static/templates/admin/*.hbs`
  - `src/static/templates/email/*.hbs`

官方 `1.37.0` 完整模板统计为 72 个（`404.hbs` 1 个、`admin/` 6 个、`email/` 63 个、`scss/` 2 个）。本项目默认发布包仅覆盖 `admin/` 与 `email/` 模板；未纳入 `404`、`scss` 等不属于本翻译目标的官方内置模板，以减少不必要的维护边界。

与官方 `1.36.0` 相比，`1.37.0` 的 `admin/` 与 `email/` 目录 Git tree 及全部文件内容完全一致；官方仅调整了本项目不覆盖的 `scss/vaultwarden.scss.hbs`。因此本次同步只更新上游基线、兼容声明和发布元数据，不修改中文模板内容。

`1.37.0` 还在 `src/config.rs` 新增了 `Trusted proxies`、`Seconds between unauthenticated requests`、`Max burst size for unauthenticated requests` 三项动态配置文档。它们通过 `CONFIG.prepare_json()` 传入设置页，不属于 Handlebars 模板中的固定文案，因此与其他配置项名称和说明一样不在本纯模板覆盖包的翻译范围内。

运行时这属于“部分模板覆盖”，不是完整替换：vaultwarden 会注册内置模板路径作为缺省来源，再叠加 data 目录中的同名模板覆盖。也就是说，`/data/templates` 中不存在的 `404.hbs` 与 `scss/*` 会继续使用当前 vaultwarden 程序自带版本；只有本项目提供的 `admin/*.hbs`、`email/*.hbs` 会被中文模板覆盖。发布包不要包含来自其他实例或不同版本的 `404.hbs`/`scss`，以免引入版本不匹配的页面或样式行为。

`upstream/1.37.0/admin` 与 `upstream/1.37.0/email` 保存用于校验的官方模板基线。

同时维护：

- `upstream/1.37.0/manifest.json`：记录清单格式版本、上游仓库、tag、commit、官方模板路径、纳入范围、文件总数和文件列表。
- `upstream/1.37.0/checksums.json`：记录上述文件的 SHA-256。

`make check-upstream` 或 `make check` 会运行 `scripts/check_upstream_manifest.py`，确认本仓库内保存的上游模板基线与 manifest 记录一致，并验证每个文件的 SHA-256 未变化。

## 更新流程建议

1. 将新版本官方 `admin`、`email` 模板复制到新的 `upstream/<version>/`。
2. 以官方新模板为基线更新 `templates/`。
3. 迁移已有中文译文，并翻译新增内容。
4. 为新版本生成/更新 `upstream/<version>/manifest.json` 与 `checksums.json`，运行 `make check-upstream` 确认官方基线未漂移。
5. 运行 `make check`，确认 upstream manifest、文件列表、Handlebars token 与邮件分隔符均通过。
6. 如本机已有目标 vaultwarden Docker 镜像，运行 `make smoke` 做容器级 smoke test；如需验证邮件模板的实际发送流程，可在 Linux Docker 环境运行 `SMTP_SMOKE=1 make smoke`，必要时用 `SMOKE_PORT` / `SMTP_SMOKE_PORT` 避开本地端口占用。
7. 运行 `make package` 生成发布包。
