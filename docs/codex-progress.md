# Codex Progress

## 项目目标

本项目用于每天生成美股收盘简报，并通过飞书自定义机器人推送到群聊。第一阶段目标是稳定输出一份基于行情数据的结构化报告，覆盖核心指数/ETF、AI/半导体、AI 电力、贵金属/大宗商品等关注列表，并支持本地 dry-run、正式飞书推送、GitHub Actions 手动触发，以及后续由外部定时器触发。

## 当前状态

- 已完成本地 Python 入口 `main.py`，支持 `python main.py --dry-run` 预览报告，正式运行时调用飞书 Webhook。
- 已完成行情数据抽象层，默认使用 `yfinance`，配置 `POLYGON_API_KEY` 后会优先尝试 Polygon/Massive 兼容数据源，并在失败时回退到 `yfinance`。
- 已完成最近交易日回溯逻辑：默认回溯 7 天，遇到周末或休市时从可用日线数据中选取最近有效交易日。
- 已完成单个 ticker 失败容错：单个标的拉取失败会记录 warning，并在报告中标记数据缺失，不应中断整份报告。
- 已完成飞书交互式卡片发送模块，包含原生表格样式、核心指数表、板块观察表和报告正文。
- 已完成可选模型分析模块：配置 OpenAI-compatible API 后可生成一句话判断和下一交易日观察重点；未配置时使用本地规则。
- 已完成 GitHub Actions 工作流 `.github/workflows/daily-market-report.yml`，支持 `workflow_dispatch` 手动触发，使用 Python 3.11 安装依赖后执行 `python main.py`。
- `.env` 已在 `.gitignore` 中，真实 Webhook 和 API Key 不应提交到 GitHub。
- 当前仓库可以从代码结构上本地运行，但本次文档初始化尚未实际联网运行 `python main.py --dry-run`。
- 当前是否已经部署到 GitHub：仓库已有 GitHub Actions 配置；本次未验证远端仓库、Secrets、Actions 手动触发和飞书实际接收。
- 当前是否可以本地运行：应可以；需要本地安装依赖，并确保网络可访问行情数据源。

## 最近一次工作记录

### 日期

2026-05-29

### 本次完成

- 建立 `docs/` 目录作为 Codex 跨设备接续上下文。
- 新增项目进度文档、关键决策文档、任务清单和运行手册。
- 梳理当前项目目标、已完成能力、未验证事项、运行方式、部署方式和排错入口。
- 明确后续每次阶段性修改后，需要主动更新 `docs/codex-progress.md` 和 `docs/todo.md`。

### 修改过的文件

- `docs/codex-progress.md`
- `docs/decisions.md`
- `docs/todo.md`
- `docs/runbook.md`

### 验证结果

本次主要是文档初始化，已通过读取项目文件确认以下事实：

- `README.md` 已记录本地运行、dry-run、飞书 Webhook、数据源、模型分析、休市处理、GitHub Actions 和 cron-job.org 触发方式。
- `main.py` 已实现 `--dry-run` 参数、行情拉取、报告构建、可选模型分析和飞书发送。
- `.github/workflows/daily-market-report.yml` 已存在，并支持 `workflow_dispatch`。
- `.gitignore` 已包含 `.env`、`.venv/`、`.yfinance_cache/`、`__pycache__/` 等本地文件。

本次未运行以下命令：

- `python main.py --dry-run`
- `python main.py`
- `pytest`
- `gh workflow run daily-market-report.yml`
- `gh run view --log`

原因：本次目标是建立跨设备接续文档，且行情数据和 GitHub/飞书验证依赖外部网络、Secrets 和真实 Webhook。

### 遇到的问题

- 当前存在一个未跟踪文件 `codex_context_ai_infra_hbm_13_f_may_2026.md`，本次未改动。后续可判断是否迁移到 `docs/` 或保留为独立资料。
- 本次无法仅凭本地文件确认 GitHub Secrets 是否已配置、GitHub Actions 是否已经在远端成功执行、飞书是否能收到真实消息。

### 未解决问题

- 尚未实际验证本地 dry-run 是否能拉取最新行情并生成完整报告。
- 尚未实际验证正式飞书推送。
- 尚未实际验证 GitHub Actions 手动触发和日志。
- 尚未确认远端 GitHub Secrets 中是否已配置 `FEISHU_WEBHOOK`、`POLYGON_API_KEY`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
- 尚未决定是否把旧的 `codex_context_ai_infra_hbm_13_f_may_2026.md` 纳入新的 `docs/` 体系。

### 下一步建议

- 先在本地执行 `python main.py --dry-run`，确认依赖安装、行情数据拉取和报告格式。
- 确认 `.env` 未被 Git 跟踪，且 `.env.example` 保持占位示例。
- 配置或检查 GitHub Secrets，至少确认 `FEISHU_WEBHOOK` 已存在。
- 手动触发 GitHub Actions，查看日志并确认飞书群收到消息。
- 若 dry-run 或 Actions 失败，把错误日志追加到本文件的历史记录，并同步更新 `docs/todo.md`。

## 历史记录

后续每次完成阶段性任务，都在这里追加一条记录，不要覆盖旧记录。
