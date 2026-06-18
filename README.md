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
python scripts/build_preview_csv.py
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

## 质量状态

```text
PASS = 数据可用于 CNSV 主系统
WARN = 可用于观察，但下游应降低置信度
FAIL = 不得用于正式信号
```

如果数据异常，宁可输出 `FAIL`，也不能伪装成正常数据。
