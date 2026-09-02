# Runbook

## 本地运行

安装依赖：

```bash
python -m pip install -r requirements.txt
```

检查当前是否处于开盘观察窗口：

```bash
python main.py --open-watch --check-window
```

本地预览开盘观察，不发送飞书：

```bash
python main.py --open-watch --dry-run
```

本地预览并写入 JSON：

```bash
python main.py --open-watch --dry-run --write-output
```

强制生成并发送飞书：

```bash
python main.py --open-watch --force-send
```

## GitHub Actions 测试

进入 GitHub 仓库 `Actions`，选择 `Open Watch`，点击 `Run workflow`。

- `force_send=true`：忽略时间窗口，用于测试发送。
- `write_output=true`：写入并自动提交 `data/open_watch/` JSON。

## 常见报错

### `FEISHU_WEBHOOK 未配置`

正式发送需要在本地 `.env` 或 GitHub Secrets 中配置 `FEISHU_WEBHOOK`。只想预览请用 `--dry-run`。

### 行情数据缺失

单个 ticker 失败不会中断整份报告。报告会在 `limitations` 中记录，并在飞书内容中标记数据缺失。

### 当前不在窗口

正式定时运行只在纽约时间 09:58-10:12 ET 发送。测试发送请加 `--force-send`。

### GitHub 没有自动提交 JSON

确认 workflow 已配置：

```yaml
permissions:
  contents: write
```

并确认 `write_output=true` 或 schedule 触发时确实产生了 `data/open_watch/` 文件变化。

## 收盘日报定时

收盘日报有两层触发：

- cron-job.org：北京时间周二到周六 09:05 调用 `Daily Market Report`。
- GitHub schedule：北京时间周二到周六约 09:12 兜底触发。

正式 workflow 会在飞书发送成功后更新 `data/daily_market/latest_sent.json`。如果两层触发都运行，后运行的一次会看到同一报告日期已经发送过，并跳过重复推送。
