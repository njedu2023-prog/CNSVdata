# CNSVdata

`CNSVdata` 是 `CNSV` 中国船舶实盘人工量化波段系统的上游数据底座仓库。

本仓库只负责数据采集、标准化、质量检查、快照、血缘和下游数据契约，不生成买卖信号、不输出交易建议、不做模型预测。

## 标的

```text
ts_code: 600150.SH
name: 中国船舶
market: A 股 / 上交所
```

## TUSHARE_TOKEN

Tushare Token 只能配置在 GitHub Actions Secrets 中：

```text
TUSHARE_TOKEN
```

代码只通过环境变量读取 Token。不要把真实 Token 写入代码、配置、README、日志、JSON、CSV 或 Parquet 元数据。

## 手动运行

```bash
pip install -r requirements.txt
export TUSHARE_TOKEN="..."

python scripts/fetch_trade_calendar.py
python scripts/fetch_cnsv_daily.py
python scripts/fetch_cnsv_1min.py
python scripts/fetch_moneyflow.py
python scripts/build_minute_bars.py
python scripts/build_corporate_actions.py
python scripts/build_structural_breaks.py
python scripts/build_data_manifest.py
python scripts/quality_check.py
pytest
```

## GitHub Actions

北京时间对应 UTC 定时：

```text
fetch_daily.yml         16:10 BJT / 08:10 UTC
fetch_minute.yml        16:20 BJT / 08:20 UTC
build_processed.yml     16:30 BJT / 08:30 UTC
data_quality_check.yml  16:40 BJT / 08:40 UTC
```

## CNSV 下游读取文件

```text
data/processed/trade_calendar.parquet
data/processed/cnsv_daily.parquet
data/processed/cnsv_1min.parquet
data/processed/cnsv_5min.parquet
data/processed/cnsv_15min.parquet
data/processed/cnsv_30min.parquet
data/processed/cnsv_60min.parquet
data/processed/cnsv_moneyflow.parquet
data/processed/corporate_actions.parquet
data/processed/structural_breaks.parquet
metadata/latest_trade_date.json
metadata/next_trade_date.json
metadata/data_manifest.json
data/quality/data_quality_latest.json
```

## 人工预览文件

GitHub 不能直接把 Parquet 展开成表格。仓库会额外生成 CSV 预览文件，方便人工在网页上查看最近数据：

```text
data/preview/trade_calendar_latest.csv
data/preview/cnsv_daily_latest.csv
data/preview/cnsv_moneyflow_latest.csv
data/preview/cnsv_1min_latest.csv
data/preview/cnsv_5min_latest.csv
data/preview/cnsv_15min_latest.csv
data/preview/cnsv_30min_latest.csv
data/preview/cnsv_60min_latest.csv
data/preview/corporate_actions.csv
data/preview/structural_breaks.csv
data/preview/preview_manifest.csv
```

CSV 只用于人工检查；CNSV 正式读取仍以 `processed/*.parquet` 为准。

## V1.1 专业验收闭环

V1.1 新增专业验收与下游读取闭环：

```text
data/quality/acceptance_latest.json
data/quality/downstream_smoke_latest.json
.github/workflows/acceptance.yml
```

验收顺序：

```text
1. pytest
2. quality_check.py
3. acceptance_check.py
4. smoke_downstream_read.py
```

只有当 `quality`、`acceptance`、`downstream smoke` 全部 `PASS` 时，CNSV 主系统才应正常读取。  
如果为 `WARN`，下游可读取但必须降低置信度。  
如果为 `FAIL`，下游不得生成正式交易辅助结果。

## V1.2 运维与验收流程

V1.2 把验收闭环升级为可定位、可追溯、可回补、可供下游安全读取的生产流程。

每日正常链路：

```text
fetch_daily
fetch_minute
build_processed
data_quality_check
acceptance
archive_quality_snapshot
```

手动复检命令：

```bash
pip install -r requirements.txt
pytest
python scripts/detect_data_gaps.py
python scripts/quality_check.py
python scripts/build_data_manifest.py
python scripts/acceptance_check.py
python scripts/smoke_downstream_read.py
python scripts/build_downstream_ready.py
python scripts/build_failure_summary.py
python scripts/archive_quality_snapshot.py
```

失败定位优先级：

```text
1. data/quality/failure_summary_latest.md
2. data/quality/acceptance_latest.json
3. data/quality/downstream_smoke_latest.json
4. data/quality/data_quality_latest.json
5. GitHub Actions logs
```

缺口检测与回补：

```bash
python scripts/detect_data_gaps.py
python scripts/backfill_missing_data.py --from-gap-report
python scripts/backfill_missing_data.py --start-date 20260601 --end-date 20260618 --daily
python scripts/backfill_missing_data.py --start-date 20260601 --end-date 20260618 --minute
python scripts/backfill_missing_data.py --start-date 20260601 --end-date 20260618 --moneyflow
```

CNSV 主系统应优先读取：

```text
metadata/downstream_ready.json
```

读取规则：

```text
ready = true  -> 可以读取
ready = false -> 不得生成正式交易辅助结果
status = WARN -> 可观察，但必须降低置信度
status = FAIL -> 阻断
```

历史追溯文件会归档到：

```text
data/quality/history/YYYY-MM-DD/
metadata/history/YYYY-MM-DD/
```

## 质量状态

```text
PASS = 数据可用于 CNSV 主系统
WARN = 可用于观察，但下游应降低置信度
FAIL = 不得用于正式信号
```

如果数据异常，宁可输出 `FAIL`，也不能伪装成正常数据。
