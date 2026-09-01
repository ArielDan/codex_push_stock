# Codex Progress

## 2026-09-01

本次在现有 `ArielDan/codex_push_stock` 项目上新增「美股开盘后 30 分钟观察」功能，没有重建项目，也没有新增 H5 Dashboard 或 `frontend/`。

## 修改文件

- `main.py`：新增 `--open-watch` 分支，并保留原收盘日报默认逻辑。
- `market_calendar.py`：新增纽约时间 09:58-10:12 ET 的开盘观察窗口判断。
- `data_sources/base.py`：新增 `IntradayBar`。
- `data_sources/yfinance_source.py`：新增 yfinance 盘中数据拉取。
- `data_sources/polygon_source.py`：新增 Polygon/Massive 盘中数据拉取。
- `technical_analysis.py`：新增 VWAP、开盘区间、趋势标签和观察型建议计算。
- `open_watch.py`：新增开盘观察报告 JSON、飞书文本和文件输出。
- `feishu.py`：新增开盘观察发送入口，复用已有飞书发送能力。
- `.github/workflows/open-watch.yml`：新增开盘观察 workflow。
- `tests/test_market_calendar.py`：新增开盘观察窗口测试。
- `README.md`、`docs/decisions.md`、`docs/todo.md`、`docs/runbook.md`：补齐跨设备接续说明。

## 验证结果

- `python main.py --open-watch --check-window`
- `python main.py --open-watch --dry-run`
- `python main.py --open-watch --dry-run --write-output`
- `python main.py --dry-run`
- `python -m unittest`

## 已知问题

- 成交量相对过去 N 日同时间段均量暂未实现，避免在没有稳定数据时硬写假信号。
- 非股票类 ticker 在 Polygon 里可能不支持，会自动 fallback 到 yfinance。
- 盘中数据依赖外部行情源，网络或数据源延迟时会标记数据缺失，不会编造结果。

## 下一步

- 增加同时间段历史成交量基准。
- 按用户持仓权重筛选更短的重点资产列表。
- 如后续需要复盘页面，再单独设计 frontend/H5，不和本次功能耦合。
