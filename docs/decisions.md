# Decisions

## 决策记录模板

### 决策标题

- 日期：
- 背景：
- 选择：
- 原因：
- 替代方案：
- 影响：
- 后续是否需要复盘：

## 当前关键决策

### 使用 GitHub Actions 作为云端运行入口

- 日期：2026-05-29
- 背景：项目需要在用户不打开本机的情况下定期生成并发送每日美股收盘简报。
- 选择：使用 GitHub Actions 执行 `python main.py`，工作流保留 `workflow_dispatch` 手动触发能力。
- 原因：代码和自动化配置都在同一个 GitHub 仓库内，换设备后只要 `git pull` 就能看到运行逻辑；GitHub Secrets 也适合保存飞书 Webhook 和 API Key。
- 替代方案：本机 cron、云服务器、飞书开放平台定时任务、Serverless 平台。
- 影响：需要在 GitHub 仓库配置 Secrets；GitHub Actions 的原生 schedule 可能偶发延迟或不触发，因此 README 建议用 cron-job.org 调用 workflow dispatch API。
- 后续是否需要复盘：需要。若稳定性或频率要求提高，可以改为云服务器、Serverless 或更稳定的调度服务。

### 第一版使用飞书自定义机器人 Webhook

- 日期：2026-05-29
- 背景：项目需要把日报发送到飞书群，但第一版重点是快速打通 MVP。
- 选择：使用飞书自定义机器人 Webhook，而不是飞书 CLI 或开放平台应用。
- 原因：Webhook 接入成本低，只需要一个 URL；适合单向推送日报；不需要复杂的 OAuth、应用审核、事件订阅和权限管理。
- 替代方案：飞书开放平台机器人应用、飞书 CLI、交互式应用卡片配合后端服务。
- 影响：当前主要支持单向推送，不适合复杂交互和用户身份相关能力。
- 后续是否需要复盘：需要。若要支持飞书内交互式查询、按钮回调或用户级权限，应升级为飞书开放平台应用。

### 默认使用 yfinance，并预留 Polygon/Massive

- 日期：2026-05-29
- 背景：项目需要获取美股、ETF、指数和大宗商品相关行情，用于每日收盘简报。
- 选择：默认使用 `yfinance`；当存在 `POLYGON_API_KEY` 时优先尝试 Polygon/Massive 兼容接口，失败后回退到 `yfinance`。
- 原因：`yfinance` 免费、接入快，适合个人 MVP；Polygon/Massive 更适合作为后续更稳定的数据源；抽象 `data_sources` 可以降低替换成本。
- 替代方案：只用 Polygon/Massive、只用 yfinance、接入 Alpha Vantage、Finnhub、Twelve Data 或券商 API。
- 影响：MVP 可快速运行，但 `yfinance` 可能受网络、限流、ticker 支持差异影响；配置 Polygon/Massive 后仍需处理指数、特殊 ticker 和商品代理 ticker 的兼容问题。
- 后续是否需要复盘：需要。若日报成为稳定依赖，应评估把 Polygon/Massive 设为主数据源，并增加数据质量校验。

### 不提交 `.env` 到 GitHub

- 日期：2026-05-29
- 背景：本地 `.env` 会保存飞书 Webhook、Polygon/Massive Key、LLM API Key 等敏感信息。
- 选择：`.env` 加入 `.gitignore`，只提交 `.env.example` 作为配置模板。
- 原因：避免泄露真实 Webhook 和 API Key；GitHub 端使用 repository secrets 注入运行环境。
- 替代方案：把配置写入代码、提交加密配置文件、使用专门的密钥管理服务。
- 影响：换电脑后需要重新创建本地 `.env`；远端 Actions 需要单独配置 Secrets。
- 后续是否需要复盘：一般不需要。若密钥数量增加，可考虑引入 1Password、Doppler 或云厂商 Secret Manager。

### 把 Codex 工作过程写入 `docs/`

- 日期：2026-05-29
- 背景：Codex 对话历史主要保存在本地设备，换电脑后不方便接续项目上下文。
- 选择：在项目仓库内建立 `docs/codex-progress.md`、`docs/decisions.md`、`docs/todo.md`、`docs/runbook.md`。
- 原因：文档随代码一起进入 Git 历史，另一台电脑 `git pull` 后 Codex 可以直接读取项目状态、决策、排错记录和下一步任务。
- 替代方案：依赖本地 Codex 历史、使用外部笔记软件、把上下文写在 README、使用 GitHub Issues。
- 影响：每次阶段性修改后需要主动维护 `docs/codex-progress.md` 和 `docs/todo.md`，否则文档会逐渐失真。
- 后续是否需要复盘：需要。若项目变复杂，可以增加 ADR、CHANGELOG、故障记录或发布记录。

### 报告只基于行情数据，不编造新闻归因

- 日期：2026-05-29
- 背景：当前项目尚未接入新闻数据源，但日报容易让人期待“为什么上涨/下跌”的原因解释。
- 选择：当前报告和模型提示都限制在行情数据范围内分析，不编造新闻或事件归因。
- 原因：避免错误归因；在没有新闻源和引用链路前，只做价格、涨跌幅、板块相对强弱和观察重点更稳妥。
- 替代方案：直接让模型自由解释行情原因、人工维护新闻、接入新闻 API 后做引用式归因。
- 影响：报告解释力会更克制，但可信度更高。
- 后续是否需要复盘：需要。接入新闻数据源后，可以新增带来源的市场归因模块。
