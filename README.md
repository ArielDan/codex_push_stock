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

## 美股开盘 30 分钟观察

开盘观察用于在美股常规开盘后约 30 分钟生成盘中走势、技术判断和观察型操作建议，并通过飞书推送。

本功能不影响原有收盘日报。默认运行 `python main.py` 仍然是收盘日报，只有显式添加 `--open-watch` 才会进入开盘观察。

检查当前是否处于开盘观察窗口：

```bash
python main.py --open-watch --check-window
```

本地预览，不发送飞书：

```bash
python main.py --open-watch --dry-run
```

本地预览并写入 JSON：

```bash
python main.py --open-watch --dry-run --write-output
```

强制生成并发送飞书，用于测试：

```bash
python main.py --open-watch --force-send
```

强制发送并写入 JSON：

```bash
python main.py --open-watch --force-send --write-output
```

开盘观察窗口使用纽约时间判断，不写死北京时间。当前允许窗口为纽约时间 09:58-10:12，覆盖美股夏令时和冬令时差异。非交易日或不在窗口内会正常退出，不报错。

## 开盘观察 JSON 输出

添加 `--write-output` 后会写入：

- `data/open_watch/latest.json`
- `data/open_watch/reports/YYYY-MM-DD.json`
- `data/open_watch/index.json`

`--dry-run` 默认不写文件，除非显式加 `--write-output`。

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

程序会回溯最近 7 天的有效交易数据。正式定时推送只在「北京时间触发时对应的纽约日期是美股交易日」才发送，避免周日/周一重复推送上周五行情。如果 7 天内核心 ETF 都没有有效数据，会推送「昨日美股休市/无交易数据」。

## 如何维护 watchlist.json

编辑 `watchlist.json`：

- 新增资产：在对应分组的 `assets` 里添加 `ticker`、`name`、`note`。
- 删除资产：删除对应字典。
- 新增分组：添加一个带 `key`、`title`、`assets` 的分组对象。
- 调整展示顺序：直接调整分组顺序或分组内 `assets` 顺序；收盘日报、开盘观察、JSON 输出和飞书推送都会按这个顺序展示。
- 修改显示后缀：例如 `^TNX` 可设置 `"display_suffix": "%"`。

`watchlist.json` 是唯一观察资产配置源。不要新增 YAML watchlist，也不要把 ticker 写死在 Python 代码里。

## GitHub Actions 部署

工作流文件位于 `.github/workflows/daily-market-report.yml`，配置如下：

- 支持手动触发：`workflow_dispatch`。
- 运行 Python 3.11。
- 安装 `requirements.txt` 后执行 `python main.py`。
- 支持 GitHub schedule 兜底触发：北京时间周二到周六约 09:12。
- 也可以继续使用 cron-job.org 调用 GitHub workflow dispatch API。
- 正式 workflow 会在发送成功后写入 `data/daily_market/latest_sent.json`，避免 cron-job.org 和 GitHub schedule 双触发时重复推送同一天收盘日报。

开盘观察工作流位于 `.github/workflows/open-watch.yml`，配置如下：

- 支持手动触发：`workflow_dispatch`。
- 支持 `force_send` 和 `write_output` 输入参数。
- 运行 Python 3.11。
- 安装 `requirements.txt` 后执行 `python main.py --open-watch`。
- GitHub schedule 同时保留 `14:00 UTC` 和 `15:00 UTC` 两个触发，由代码内部判断纽约时间窗口，适配夏令时/冬令时。
- 如果 `data/open_watch/` 有变化，会自动 commit 并 push；没有变化则不提交。

## GitHub Secrets 配置

在 GitHub 仓库页面进入：

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

添加：

- `FEISHU_WEBHOOK`：必填，飞书自定义机器人 Webhook。
- `POLYGON_API_KEY`：可选，Polygon/Massive API Key。
- `LLM_API_KEY`：可选，模型 API Key。
- `LLM_BASE_URL`：可选，OpenAI-compatible API Base URL。
- `LLM_MODEL`：可选，模型名称。

## 手动触发 GitHub Actions

进入 GitHub 仓库的 `Actions` 页面，选择 `Daily Market Report`，点击 `Run workflow`。

开盘观察手动触发：

1. 进入 GitHub 仓库的 `Actions` 页面。
2. 选择 `Open Watch`。
3. 点击 `Run workflow`。
4. 测试发送时可选择 `force_send=true`。
5. 需要写入 JSON 时选择 `write_output=true`。

## docs 跨设备接续

`docs/` 目录用于跨电脑接续项目上下文：

- `docs/investment-analyst-playbook.md`：投资分析框架。
- `docs/codex-progress.md`：开发进展、修改文件、验证结果、已知问题和下一步。
- `docs/decisions.md`：关键技术和产品决策。
- `docs/todo.md`：P0/P1/P2 待办。
- `docs/runbook.md`：本地运行、Actions 测试和常见报错。

## H5 Dashboard

当前项目只实现飞书推送和 JSON 沉淀。H5 Dashboard 暂不实现，也不新增 `frontend/`。后续如果需要 review 页面，再单独新增前端能力。

## cron-job.org 定时触发

建议用 cron-job.org 在北京时间周二到周六 9:05 调用 GitHub Actions 手动触发接口。北京时间周六早上对应纽约周五收盘后，因此需要保留周六触发；北京时间周日和周一会对应纽约周六/周日，程序会自动跳过，避免重复推送周五行情。

仓库同时保留 GitHub schedule 作为兜底触发。cron-job.org 如果正常先触发并发送成功，会写入已发送状态；GitHub schedule 随后触发时会自动跳过同一天报告。

请求配置：

- URL: `https://api.github.com/repos/ArielDan/codex_push_stock/actions/workflows/daily-market-report.yml/dispatches`
- Method: `POST`
- Timezone: `Asia/Shanghai`
- Schedule: 周二到周六 `09:05`
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

正式推送默认只发送本次触发对应的新美股收盘数据。判断基准是纽约日期是否为美股交易日：北京时间周二到周六通常分别推送美股周一到周五；北京时间周日、周一或美国休市日会自动跳过。如果需要测试正式发送，可以手动运行：

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
