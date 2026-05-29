# Runbook

## 本地首次运行

```bash
git pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
open .env
```

在 `.env` 中至少按需配置：

```bash
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token
POLYGON_API_KEY=
LLM_API_KEY=
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=
```

本地只预览报告时，可以不配置 `FEISHU_WEBHOOK`，直接使用 dry-run。

## 本地 dry-run

```bash
source .venv/bin/activate
python main.py --dry-run
```

预期结果：

- 程序会拉取行情数据并在终端打印报告。
- 不会发送飞书消息。
- 不要求配置 `FEISHU_WEBHOOK`。

如果系统没有 `python` 命令，可改用：

```bash
python3 main.py --dry-run
```

或按本机安装情况使用 `python3.11`。

## 本地正式发送

```bash
source .venv/bin/activate
python main.py
```

预期结果：

- 程序读取 `.env` 中的 `FEISHU_WEBHOOK`。
- 生成报告后通过飞书自定义机器人发送到群聊。
- 成功时日志显示飞书推送完成。

## GitHub Actions 部署

工作流文件：

```text
.github/workflows/daily-market-report.yml
```

当前工作流能力：

- 支持 `workflow_dispatch` 手动触发。
- 使用 `ubuntu-latest`。
- 使用 Python 3.11。
- 安装 `requirements.txt`。
- 注入 GitHub Secrets 后执行 `python main.py`。

需要在 GitHub 仓库中配置：

- `FEISHU_WEBHOOK`：必填，飞书自定义机器人 Webhook。
- `POLYGON_API_KEY`：可选，Polygon/Massive API Key。
- `LLM_API_KEY`：可选，OpenAI-compatible 模型 API Key。
- `LLM_BASE_URL`：可选，模型服务 base URL 或完整 `/chat/completions` 地址。
- `LLM_MODEL`：可选，模型名称。

配置入口：

```text
GitHub 仓库 -> Settings -> Secrets and variables -> Actions -> New repository secret
```

## 手动触发 GitHub Actions

在 GitHub 页面触发：

```text
Actions -> Daily Market Report -> Run workflow
```

使用 GitHub CLI 触发：

```bash
gh workflow run daily-market-report.yml
```

查看最近运行：

```bash
gh run list --workflow daily-market-report.yml
gh run view --log
```

## 定时触发建议

当前 README 建议使用 cron-job.org 每天北京时间 09:05 调用 GitHub workflow dispatch API，避免 GitHub Actions 原生 schedule 偶发延迟或不触发。

请求示例：

```text
POST https://api.github.com/repos/ArielDan/codex_push_stock/actions/workflows/daily-market-report.yml/dispatches
```

Headers：

```text
Authorization: Bearer <GitHub token>
Accept: application/vnd.github+json
Content-Type: application/json
```

Body：

```json
{"ref":"main"}
```

GitHub token 建议使用 fine-grained personal access token，只授权本仓库 `Actions: Read and write`。

## 常见排错

### `FEISHU_WEBHOOK 未配置`

原因：

- 正式运行 `python main.py` 时没有配置 `FEISHU_WEBHOOK`。
- GitHub Actions 中没有配置同名 Secret。

处理：

- 本地调试使用 `python main.py --dry-run`。
- 正式发送前在 `.env` 或 GitHub Secrets 中配置 `FEISHU_WEBHOOK`。

### 飞书发送失败

原因可能包括：

- Webhook URL 错误或已失效。
- 飞书机器人安全设置要求关键词、签名或 IP 白名单。
- 飞书 API 返回非 2xx 状态码。

处理：

- 查看程序打印的 HTTP 状态码和响应内容。
- 确认飞书群里的自定义机器人仍可用。
- 若启用了安全关键词，确保报告内容包含关键词，或调整机器人安全配置。

### yfinance 拉取失败

原因可能包括：

- 本地或 GitHub Actions 网络访问异常。
- Yahoo 数据源临时限制。
- 特殊 ticker 不支持或返回空数据。

处理：

- 稍后重试 `python main.py --dry-run`。
- 检查网络。
- 配置 `POLYGON_API_KEY` 作为优先数据源。
- 对长期缺失的 ticker，考虑替换为更稳定的代理标的。

### Polygon/Massive 拉取失败

原因可能包括：

- `POLYGON_API_KEY` 未配置或无权限。
- 免费套餐不支持某些资产类型。
- 指数、带 `^` 的 ticker 或特殊商品代理不在当前 MVP 支持范围内。

处理：

- 确认 API Key 可用。
- 查看日志中具体 ticker 和 HTTP 响应。
- 当前代码会回退到 `yfinance`，若回退也失败，需要调整 watchlist 或数据源逻辑。

### GitHub Actions 没有收到 Secret

原因：

- Secret 名称拼写不一致。
- Secret 配在了其他仓库或环境。
- workflow 运行的 ref 不是预期分支。

处理：

- 检查 workflow 中的环境变量名。
- 在 GitHub 仓库 Secrets 页面确认名称。
- 手动触发后用 `gh run view --log` 查看错误。

## 换电脑接续流程

```bash
git pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
open .env
```

然后让 Codex 优先读取：

- `docs/codex-progress.md`
- `docs/todo.md`
- `docs/decisions.md`
- `docs/runbook.md`

继续工作时，优先处理 `docs/todo.md` 中的 P0 事项。完成阶段性修改后，更新 `docs/codex-progress.md` 和 `docs/todo.md`，再随代码一起提交到 GitHub。
