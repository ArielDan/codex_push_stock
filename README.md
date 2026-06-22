# 每日美股收盘简报飞书推送 Bot

每天北京时间 9:00 自动生成「前一日美股收盘简报」，并通过飞书自定义机器人 Webhook 推送。报告只基于行情数据做结构化总结，不编造新闻归因。

## 环境要求

- 建议 Python 3.11 或 3.12。
- GitHub Actions 默认使用 Python 3.11。
- 本机如只有旧版 Python，请先安装 3.11+；部分行情依赖在更新 Python 版本上更稳定。

## 本地运行

```bash
python -m pip install -r requirements.txt
python main.py --dry-run
```

如果你的系统没有 `python` 命令，可以改用 `python3.11`：

```bash
python3.11 -m pip install -r requirements.txt
python3.11 main.py --dry-run
```

## dry-run

```bash
python main.py --dry-run
```

`--dry-run` 只打印报告内容，不发送飞书，也不要求配置 `FEISHU_WEBHOOK`，适合本地调试数据和格式。

## 飞书 Webhook 配置

1. 在飞书群中添加「自定义机器人」。
2. 复制机器人 Webhook 地址。
3. 在本地创建 `.env`：

```bash
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
POLYGON_API_KEY=
```

`.env` 已加入 `.gitignore`，不要提交真实 Webhook 或密钥。

配置好后发送正式消息：

```bash
python main.py
```

如果飞书发送失败，程序会打印 HTTP 状态码和响应内容。

## 数据源说明

- 默认使用 `yfinance`，适合个人自用 MVP。
- 当环境变量 `POLYGON_API_KEY` 存在时，会优先尝试 Polygon/Massive 兼容接口。
- Polygon 拉取失败、特殊 ticker 不支持或单个 ticker 异常时，会 fallback 到 `yfinance`。
- 单个 ticker 拉取失败不会中断整份报告；报告会标记「数据缺失」或跳过汇总。

## 模型分析

「一句话判断」和「下一交易日观察重点」支持接入 OpenAI-compatible 模型 API。未配置模型时，会自动使用本地规则判断。

在 `.env` 或 GitHub Secrets 中配置：

```bash
LLM_API_KEY=你的模型 API Key
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=你的模型名称
```

程序会调用 `${LLM_BASE_URL}/chat/completions`。如果你的服务商给的是完整 `/chat/completions` 地址，也可以直接填完整地址。模型会返回一句行情判断和 3 条下一交易日观察重点。prompt 已限制只能基于行情数据分析，不允许编造新闻归因。

## 休市处理

程序会回溯最近 7 天的有效交易数据。北京时间周一 9:00 运行时，美国仍是周日晚上，程序会自动使用上一个有效美股交易日的数据。如果 7 天内核心 ETF 都没有有效数据，会推送「昨日美股休市/无交易数据」。

## 修改或新增 ticker

编辑 `watchlist.json`：

- 新增资产：在对应分组的 `assets` 里添加 `ticker`、`name`、`note`。
- 删除资产：删除对应字典。
- 新增分组：添加一个带 `key`、`title`、`assets` 的分组对象。
- 修改显示后缀：例如 `^TNX` 可设置 `"display_suffix": "%"`。

## GitHub Actions 部署

工作流文件位于 `.github/workflows/daily-market-report.yml`，配置如下：

- 支持手动触发：`workflow_dispatch`。
- 运行 Python 3.11。
- 安装 `requirements.txt` 后执行 `python main.py`。
- 定时触发建议使用 cron-job.org 调用 GitHub workflow dispatch API，避免 GitHub schedule 偶发不触发。

## GitHub Secrets 配置

在 GitHub 仓库页面进入：

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

添加：

- `FEISHU_WEBHOOK`：必填，飞书自定义机器人 Webhook。
- `POLYGON_API_KEY`：可选，Polygon/Massive API Key。

## 手动触发 GitHub Actions

进入 GitHub 仓库的 `Actions` 页面，选择 `Daily Market Report`，点击 `Run workflow`。

## cron-job.org 定时触发

建议用 cron-job.org 在北京时间周一到周五 9:05 调用 GitHub Actions 手动触发接口。程序内部也会判断本次触发是否对应新的美股收盘交易日；如果遇到美国节假日或北京时间周末，不会重复推送旧行情。

请求配置：

- URL: `https://api.github.com/repos/ArielDan/codex_push_stock/actions/workflows/daily-market-report.yml/dispatches`
- Method: `POST`
- Timezone: `Asia/Shanghai`
- Schedule: 周一到周五 `09:05`
- Headers:

```text
Authorization: Bearer <GitHub token>
Accept: application/vnd.github+json
Content-Type: application/json
```

Body:

```json
{"ref":"main"}
```

GitHub token 建议使用 fine-grained personal access token，只授权本仓库 `Actions: Read and write`。

## 修改推送时间

在 cron-job.org 修改任务的执行时间即可。GitHub workflow 本身只保留 `workflow_dispatch`，不再依赖 GitHub schedule。

## 休市日和强制发送

正式推送默认只发送本次触发对应的新美股收盘数据。北京时间周末、美国休市日、或最新行情日期仍是旧数据时，会自动跳过。如果需要测试正式发送，可以手动运行：

```bash
python main.py --force
```

## 常见问题

### `FEISHU_WEBHOOK 未配置`

正式发送需要配置 `FEISHU_WEBHOOK`。本地只想看报告请使用：

```bash
python main.py --dry-run
```

### 某些 ticker 数据缺失

小票、特殊指数或代理 ticker 可能被数据源限制。程序会记录 warning，并在报告中标记「数据缺失」。

### yfinance 拉取失败

检查网络连接，稍后重试，或配置 `POLYGON_API_KEY` 使用备用数据源。

### 本机 Python 版本过旧

请安装 Python 3.11 或 3.12，并用对应命令运行：

```bash
python3.11 main.py --dry-run
```
