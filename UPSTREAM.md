# UPSTREAM

## vaultwarden

- 目标版本：`1.36.0`
- 上游仓库：`https://github.com/dani-garcia/vaultwarden`
- 上游提交：`f21a3adae2fbb8582b60b121783c597fe6895ff4`
- 官方模板相对路径：`src/static/templates`
- 纳入范围：
  - `src/static/templates/admin/*.hbs`
  - `src/static/templates/email/*.hbs`

官方 `1.36.0` 完整模板统计为 72 个（`404.hbs` 1 个、`admin/` 6 个、`email/` 63 个、`scss/` 2 个）。本项目默认发布包只覆盖用户目标所需的 `admin/` 与 `email/`，避免无必要地冻结 `404`/`scss` 等官方内置模板。

`upstream/1.36.0/admin` 与 `upstream/1.36.0/email` 保存了本翻译包校验所用的官方模板基线。

同时维护：

- `upstream/1.36.0/manifest.json`：记录 manifest schema、上游仓库/tag/commit、官方模板路径、纳入范围、文件总数和文件列表。
- `upstream/1.36.0/checksums.json`：记录上述文件的 SHA-256。

`make check-upstream` 或 `make check` 会运行 `scripts/check_upstream_manifest.py`，确认 vendored upstream 文件列表与 manifest 一致，且每个文件 SHA-256 未变化。

## 更新流程建议

1. 将新版本官方 `admin`、`email` 模板复制到新的 `upstream/<version>/`。
2. 以官方新模板为基线更新 `templates/`。
3. 迁移已有中文译文，并翻译新增内容。
4. 为新版本生成/更新 `upstream/<version>/manifest.json` 与 `checksums.json`，运行 `make check-upstream` 确认官方基线未漂移。
5. 运行 `make check`，确认 upstream manifest、文件列表、Handlebars token 与邮件分隔符均通过。
6. 如本机已有目标 vaultwarden Docker 镜像，运行 `make smoke` 做容器级 smoke test；如需验证邮件模板真实发送路径，可在 Linux Docker 环境运行 `SMTP_SMOKE=1 make smoke`，必要时用 `SMOKE_PORT` / `SMTP_SMOKE_PORT` 避开本地端口占用。
7. 运行 `make package` 生成发布包。
