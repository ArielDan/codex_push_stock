# Todo

## P0

- 确认 GitHub Secrets 中 `FEISHU_WEBHOOK` 可用。
- 手动触发 `Open Watch` workflow，测试 `force_send=true`、`write_output=true`。
- 检查 `data/open_watch/latest.json`、`reports/YYYY-MM-DD.json`、`index.json` 是否自动提交。

## P1

- 增加成交量相对过去 N 日同时间段均量。
- 为高波动小票增加最小成交额或数据质量提示。
- 优化飞书卡片长度，必要时只展示核心分组，完整数据保留在 JSON。

## P2

- 接入更稳定的盘中行情源。
- 增加收盘后对开盘观察结论的命中复盘。
- 后续如需要 review 页面，再新增 frontend/H5。
