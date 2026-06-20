# CNSVdata 双数据线独立化改造开发文档

项目：CNSVdata  
目标：日线数据线 与 盘中线数据线 完全独立  
适用对象：Codex 开发执行  
优先级：最高  
开发原则：不推倒重来，不破坏现有日线主链，在当前仓库基础上完成专业级架构隔离。

---

# 一、本次修改的核心背景

CNSVdata 仓库现在同时承担两类数据职责：

1. CNSV 日线主程序所需的数据底座。
2. CNSV 盘中线主程序所需的数据底座。

这两套数据未来在 CNSV 主仓库中分别对应独立主程序：

- CNSV 日线主程序
- CNSV 盘中线主程序

因此，CNSVdata 内部必须拆成两条互相独立的数据线。

本次改造的最高原则是：

日线数据线和盘中线数据线允许共用同一个 GitHub 仓库，但不允许共用 ready、manifest、quality、workflow、下游读取契约和核心数据产物。

---

# 二、必须解决的核心问题

当前 CNSVdata 已经有旧的日线 / 分钟 / 资金流数据主链，状态可以 PASS。

但新加的 CNSV 盘中线不能继续混用旧路径，例如：

- data/processed/cnsv_daily.parquet
- data/processed/cnsv_1min.parquet
- metadata/downstream_ready.json
- metadata/data_manifest.json
- data/quality/data_quality_latest.json

这些旧路径可以作为 legacy 兼容层保留，但盘中线不得依赖它们作为正式输入。

特别注意：

cnsvdata/intraday.py 里的 read_source_minutes() 目前如果找不到盘中线自己的 raw 文件，会 fallback 到 data/processed/cnsv_1min.parquet。

这个逻辑必须删除。

盘中线自己的分钟数据不存在时，必须 FAIL，不能偷用旧 processed 文件冒充盘中线数据。

---

# 三、目标架构

## 3.1 总体结构

CNSVdata 仓库需要形成如下结构：

```text
CNSVdata
├── data
│   ├── daily
│   │   ├── raw
│   │   ├── processed
│   │   ├── preview
│   │   └── reference
│   │
│   ├── intraday
│   │   ├── raw
│   │   ├── snapshots
│   │   ├── replay
│   │   ├── reference
│   │   ├── labels
│   │   ├── ml_dataset
│   │   └── preview
│   │
│   └── quality
│       ├── daily
│       └── intraday
│
├── metadata
│   ├── daily
│   └── intraday
│
├── scripts
│   ├── daily_*
│   └── intraday_*
│
└── .github/workflows
    ├── daily_*.yml
    └── intraday_*.yml
```

旧路径可以暂时保留：

```text
data/processed/
metadata/data_manifest.json
metadata/downstream_ready.json
data/quality/data_quality_latest.json
```

但这些只能作为 legacy 兼容层，不允许盘中线正式读取。

---

# 四、日线数据线独立化要求

## 4.1 日线数据目录

日线数据线只能使用以下目录：

```text
data/daily/raw/
data/daily/processed/
data/daily/preview/
data/daily/reference/
data/quality/daily/
metadata/daily/
```

## 4.2 日线核心产物

日线 processed 文件建议放在：

```text
data/daily/processed/cnsv_daily.parquet
data/daily/processed/cnsv_moneyflow.parquet
data/daily/processed/corporate_actions.parquet
data/daily/processed/structural_breaks.parquet
data/daily/processed/trade_calendar.parquet
```

日线 preview 文件建议放在：

```text
data/daily/preview/cnsv_daily_latest.csv
data/daily/preview/cnsv_moneyflow_latest.csv
```

日线 quality 文件必须放在：

```text
data/quality/daily/daily_quality_latest.json
data/quality/daily/daily_gaps_latest.json
data/quality/daily/daily_acceptance_latest.json
data/quality/daily/daily_smoke_latest.json
```

日线 metadata 必须放在：

```text
metadata/daily/daily_ready.json
metadata/daily/daily_manifest.json
metadata/daily/daily_latest_trade_date.json
metadata/daily/daily_next_trade_date.json
metadata/daily/daily_downstream_contract.json
```

## 4.3 日线 ready 规则

日线 ready 文件必须独立：

```text
metadata/daily/daily_ready.json
```

字段至少包括：

```json
{
  "line": "daily",
  "repo": "CNSVdata",
  "ready": true,
  "status": "PASS",
  "latest_trade_date": "YYYYMMDD",
  "manifest_path": "metadata/daily/daily_manifest.json",
  "quality_path": "data/quality/daily/daily_quality_latest.json",
  "allowed_usage": {
    "can_run_daily_model": true,
    "can_run_daily_backtest": true,
    "can_run_intraday_model": false,
    "can_generate_formal_signal": false
  },
  "blocking_reason": null,
  "warnings": [],
  "created_at": "ISO8601"
}
```

日线 ready 只代表日线数据可用，不代表盘中线可用。

---

# 五、盘中线数据线独立化要求

## 5.1 盘中线目录

盘中线只能使用以下目录：

```text
data/intraday/raw/
data/intraday/snapshots/YYYYMMDD/1400/
data/intraday/replay/YYYYMMDD/1400/
data/intraday/reference/
data/intraday/labels/t1_truth/
data/intraday/ml_dataset/t1_intraday/
data/intraday/preview/
data/quality/intraday/
metadata/intraday/
```

禁止盘中线正式读取：

```text
data/processed/
data/daily/
metadata/daily/
metadata/downstream_ready.json
metadata/data_manifest.json
data/quality/data_quality_latest.json
```

## 5.2 盘中线 raw 数据

盘中线自己的分钟原始数据必须放在：

```text
data/intraday/raw/cnsv_1min_intraday_1400.parquet
```

或者按日期分区：

```text
data/intraday/raw/YYYYMMDD/cnsv_1min_intraday_1400.parquet
```

字段至少包括：

```text
trade_date
trade_time
ts_code
name
open
high
low
close
volume
amount
source
created_at
session
bar_index
```

时间范围必须严格限制为：

```text
09:30 - 11:30
13:00 - 14:00
```

不得包含 14:00 之后的数据。

## 5.3 盘中线 snapshot 产物

真实盘中运行产物必须写入：

```text
data/intraday/snapshots/YYYYMMDD/1400/
```

每个交易日必须生成：

```text
cnsv_1min_asof_1400.parquet
cnsv_5min_asof_1400.parquet
cnsv_15min_asof_1400.parquet
intraday_snapshot_1400.json
intraday_quality_1400.json
intraday_manifest_1400.json
intraday_ready_1400.json
```

## 5.4 盘中线 replay 产物

历史重放产物必须写入：

```text
data/intraday/replay/YYYYMMDD/1400/
```

每个历史交易日必须生成：

```text
cnsv_1min_asof_1400.parquet
cnsv_5min_asof_1400.parquet
cnsv_15min_asof_1400.parquet
intraday_snapshot_1400.json
intraday_quality_1400.json
intraday_manifest_1400.json
```

历史重放必须满足：

1. 只使用 T 日 14:00 以前数据。
2. 不得使用 T 日收盘价构造 T 日 feature。
3. 不得使用 T+1 数据构造 T 日 feature。
4. T+1 close 只能进入 label，不得进入 feature。
5. 每条 replay 必须标记 replay = true。
6. 每条真实 snapshot 必须标记 replay = false。

---

# 六、删除盘中线 fallback 到旧 processed 的逻辑

必须修改文件：

```text
cnsvdata/intraday.py
```

当前 read_source_minutes() 不允许再这样：

```text
先找 data/intraday/raw/cnsv_1min_intraday_1400.parquet
如果没有，再读 data/processed/cnsv_1min.parquet
```

必须改为：

1. 只读取盘中线自己的 raw 文件。
2. 如果 raw 文件不存在，直接返回空数据或抛出明确异常。
3. build_intraday_ready_1400.py 必须生成 FAIL。
4. reason 必须包含：

```text
missing_intraday_minute_source
```

正确逻辑：

```text
盘中线 raw 不存在 = 盘中线 FAIL
日线数据存在 = 不影响盘中线 FAIL
盘中线 FAIL = 不影响日线 PASS
```

---

# 七、盘中线 T+1 truth 独立闭环

盘中线需要 T+1 close 做真值标签，但不能直接依赖日线 ready。

应新增盘中线自己的 reference 文件：

```text
data/intraday/reference/t1_close_reference.parquet
```

该文件可以从 Tushare 独立拉取，也可以由盘中线 workflow 独立生成，但必须放在 intraday 命名空间下。

不能让盘中线 truth 直接读取：

```text
data/processed/cnsv_daily.parquet
data/daily/processed/cnsv_daily.parquet
metadata/daily/daily_ready.json
```

如果为了节省接口调用，允许共用同一个 Tushare 数据源，但必须重新写入盘中线 reference 文件，形成盘中线自己的闭环产物。

盘中线 truth 文件必须放在：

```text
data/intraday/labels/t1_truth/t1_truth_vs_1400_latest.parquet
data/intraday/labels/t1_truth/t1_truth_vs_1400_latest.csv
data/intraday/labels/t1_truth/t1_truth_manifest.json
data/intraday/labels/t1_truth/t1_truth_quality.json
```

---

# 八、盘中线训练样本必须专业化

当前如果 trainset 只有：

```text
feature_return_from_open_to_1400 = 0.0
```

这是占位，不是专业量化训练样本，必须修复。

盘中线训练样本必须放在：

```text
data/intraday/ml_dataset/t1_intraday/t1_intraday_trainset.parquet
data/intraday/ml_dataset/t1_intraday/t1_intraday_trainset_latest.csv
data/intraday/ml_dataset/t1_intraday/feature_manifest.json
data/intraday/ml_dataset/t1_intraday/label_manifest.json
data/intraday/ml_dataset/t1_intraday/trainset_quality.json
```

必须包含以下核心字段：

```text
trade_date
ts_code
asof_time
asof_price_1400
next_trade_date
next_close
actual_return_vs_1400
actual_up_label
actual_down_label
actual_flat_label
actual_limitup_label
```

必须包含以下 feature 字段：

```text
feature_return_from_open_to_1400
feature_return_from_vwap_to_1400
feature_high_drawdown_until_1400
feature_low_rebound_until_1400
feature_intraday_volatility_until_1400
feature_volume_until_1400
feature_amount_until_1400
feature_morning_volume_ratio
feature_afternoon_volume_ratio
feature_vwap_deviation
feature_price_slope_morning
feature_price_slope_afternoon
feature_volume_slope_afternoon
feature_range_until_1400
feature_close_position_until_1400
```

必须包含版本字段：

```text
feature_version = intraday_1400_v1
label_version = t1_close_vs_1400_v1
```

必须禁止以下字段进入 trainset feature：

```text
pred_up_prob
pred_down_prob
pred_return
pred_price_low
pred_price_mid
pred_price_high
model_confidence
buy_signal
sell_signal
formal_signal
manual_decision_reference
```

---

# 九、workflow 独立化要求

## 9.1 日线 workflow

日线 workflow 只能处理 daily 命名空间。

建议保留或新增：

```text
.github/workflows/daily_fetch.yml
.github/workflows/daily_build_processed.yml
.github/workflows/daily_quality_check.yml
.github/workflows/daily_acceptance.yml
```

如果为了兼容暂时保留旧文件名，也必须确保这些 workflow 不写入 intraday 命名空间。

日线 workflow git add 只能包含：

```text
data/daily
data/quality/daily
metadata/daily
```

最多加 legacy 兼容输出，但不能触碰：

```text
data/intraday
data/quality/intraday
metadata/intraday
```

## 9.2 盘中线 workflow

盘中线 workflow 只能处理 intraday 命名空间。

必须有：

```text
.github/workflows/fetch_intraday_1400.yml
.github/workflows/build_t1_truth.yml
.github/workflows/build_intraday_trainset.yml
.github/workflows/intraday_acceptance.yml
```

盘中线 workflow git add 只能包含：

```text
data/intraday
data/quality/intraday
metadata/intraday
```

禁止盘中线 workflow git add：

```text
data/processed
data/daily
metadata/daily
metadata/downstream_ready.json
metadata/data_manifest.json
data/quality/data_quality_latest.json
```

---

# 十、ready 和 downstream contract 独立化

## 10.1 日线下游契约

日线主程序只能读取：

```text
metadata/daily/daily_ready.json
metadata/daily/daily_downstream_contract.json
```

日线 contract 必须明确：

```json
{
  "line": "daily",
  "provider_repo": "CNSVdata",
  "consumer_repo": "CNSV",
  "consumer_program": "CNSV_daily_main",
  "ready_path": "metadata/daily/daily_ready.json",
  "manifest_path": "metadata/daily/daily_manifest.json",
  "can_run_daily_model": true,
  "can_run_intraday_model": false,
  "can_generate_formal_signal": false
}
```

## 10.2 盘中线下游契约

盘中线主程序只能读取：

```text
metadata/intraday/intraday_ready_1400.json
metadata/intraday/intraday_downstream_contract.json
```

盘中线 contract 必须明确：

```json
{
  "line": "intraday_1400",
  "provider_repo": "CNSVdata",
  "consumer_repo": "CNSV",
  "consumer_program": "CNSV_intraday_main",
  "ready_path": "metadata/intraday/intraday_ready_1400.json",
  "manifest_path": "metadata/intraday/intraday_manifest_1400.json",
  "can_run_daily_model": false,
  "can_run_intraday_model": true,
  "can_generate_formal_signal": false
}
```

注意：

CNSVdata 永远不得生成 formal signal。  
CNSVdata 只提供数据，不提供买卖建议，不提供预测结论。

---

# 十一、验收检查必须拆分

## 11.1 日线验收

新增或修改：

```text
scripts/daily_acceptance_check.py
scripts/daily_smoke_downstream_read.py
```

日线验收只检查：

```text
data/daily/processed/*
data/quality/daily/*
metadata/daily/*
```

日线验收不得检查 intraday 文件。

## 11.2 盘中线验收

修改：

```text
scripts/intraday_acceptance_check.py
scripts/intraday_smoke_downstream_read.py
```

盘中线验收只检查：

```text
data/intraday/*
data/quality/intraday/*
metadata/intraday/*
```

盘中线验收不得检查 daily 文件。

盘中线验收必须检查：

1. metadata/intraday/intraday_ready_1400.json 是否存在。
2. data/intraday/raw/cnsv_1min_intraday_1400.parquet 是否存在。
3. snapshots 最新交易日是否存在。
4. replay 历史快照是否存在。
5. replay 数量是否达到配置要求。
6. t1_truth 是否存在。
7. trainset 是否存在。
8. feature_version 是否存在。
9. label_version 是否存在。
10. 是否存在 forbidden prediction columns。
11. 是否存在 future leak。
12. manifest 是否覆盖所有关键文件。
13. quality 是否为 PASS / WARN / FAIL。
14. FAIL 时是否阻止 CNSV 盘中线主程序读取。

---

# 十二、历史分钟数据拉取要求

盘中线需要历史 14:00 replay，因此必须有足够历史分钟数据。

默认要求：

```text
CNSVDATA_INTRADAY_HISTORY_DAYS = 150
```

如果 Tushare 1min 历史权限不足，不能假装 PASS。

必须明确输出：

```json
{
  "status": "WARN 或 FAIL",
  "reason": "insufficient_intraday_history",
  "required_trade_days": 150,
  "actual_trade_days": 实际数量,
  "source": "tushare",
  "can_train_model": false
}
```

如果实际只有 8 个交易日，则必须 WARN 或 FAIL，不能 PASS。

---

# 十三、旧路径兼容策略

不要直接删除旧路径，避免破坏已有 CNSV 日线主程序。

旧路径可以暂时保留：

```text
data/processed/
metadata/downstream_ready.json
metadata/data_manifest.json
data/quality/data_quality_latest.json
```

但必须增加注释或 manifest 字段说明：

```text
legacy_compatibility = true
canonical_line = daily
```

正式新契约必须以以下路径为准：

```text
metadata/daily/daily_ready.json
metadata/intraday/intraday_ready_1400.json
```

后续 CNSV 主仓库改造时，再逐步切换到新路径。

---

# 十四、禁止事项

本次修改严禁：

1. 盘中线读取日线 ready。
2. 盘中线读取日线 manifest。
3. 盘中线 fallback 到 data/processed/cnsv_1min.parquet。
4. 盘中线 workflow 写入 daily 目录。
5. 日线 workflow 写入 intraday 目录。
6. 日线 PASS 推导盘中线 PASS。
7. 盘中线 FAIL 影响日线 PASS。
8. CNSVdata 输出任何预测字段。
9. CNSVdata 输出买入建议。
10. CNSVdata 输出卖出建议。
11. CNSVdata 输出 formal signal。
12. 用 T 日 14:00 之后数据构造盘中线 feature。
13. 用 T+1 close 构造 T 日 feature。
14. 用 created_at、label、actual_return 等字段构造 feature。

---

# 十五、建议修改文件清单

优先修改以下文件：

```text
cnsvdata/intraday.py
scripts/fetch_intraday_1min_1400.py
scripts/replay_intraday_1400_history.py
scripts/build_t1_truth_vs_1400.py
scripts/build_t1_intraday_trainset.py
scripts/build_intraday_manifest_1400.py
scripts/build_intraday_ready_1400.py
scripts/intraday_acceptance_check.py
scripts/intraday_smoke_downstream_read.py
```

新增或重构日线独立脚本：

```text
scripts/daily_acceptance_check.py
scripts/daily_smoke_downstream_read.py
scripts/build_daily_manifest.py
scripts/build_daily_ready.py
```

修改 workflow：

```text
.github/workflows/fetch_intraday_1400.yml
.github/workflows/build_t1_truth.yml
.github/workflows/build_intraday_trainset.yml
.github/workflows/intraday_acceptance.yml
```

必要时新增：

```text
.github/workflows/daily_acceptance.yml
.github/workflows/daily_quality_check.yml
```

新增测试：

```text
tests/test_daily_intraday_isolation.py
tests/test_intraday_no_fallback_to_daily.py
tests/test_intraday_no_future_leak.py
tests/test_intraday_ready_contract.py
tests/test_daily_ready_contract.py
```

---

# 十六、必须新增的测试用例

## 16.1 日线和盘中线互不影响

测试目标：

日线 ready = PASS 时，盘中线 raw 缺失，盘中线必须 FAIL。

预期：

```text
metadata/daily/daily_ready.json => PASS
metadata/intraday/intraday_ready_1400.json => FAIL
```

## 16.2 盘中线不得 fallback 到 data/processed

测试目标：

删除或隐藏：

```text
data/intraday/raw/cnsv_1min_intraday_1400.parquet
```

即使存在：

```text
data/processed/cnsv_1min.parquet
```

盘中线也必须 FAIL。

预期 reason：

```text
missing_intraday_minute_source
```

## 16.3 盘中线不得读取 daily ready

测试目标：

让：

```text
metadata/daily/daily_ready.json = PASS
```

同时让：

```text
metadata/intraday/intraday_ready_1400.json
```

不存在。

盘中线 smoke read 必须 FAIL。

## 16.4 future leak 检查

训练样本 feature 中不得出现：

```text
next_close
actual_return_vs_1400
actual_up_label
actual_down_label
actual_flat_label
actual_limitup_label
created_at
```

这些字段可以存在于 label 区或 metadata 区，但不得以 feature_ 前缀进入模型特征。

## 16.5 replay 数量检查

如果配置：

```text
CNSVDATA_INTRADAY_HISTORY_DAYS=150
```

实际 replay 只有 8 天，则：

```text
intraday_acceptance_latest.json
```

必须 WARN 或 FAIL，不能 PASS。

---

# 十七、运行顺序

完成修改后，先运行日线验收：

```bash
python scripts/build_daily_manifest.py
python scripts/build_daily_ready.py
python scripts/daily_acceptance_check.py
python scripts/daily_smoke_downstream_read.py
```

再运行盘中线验收：

```bash
python scripts/fetch_intraday_1min_1400.py
python scripts/build_intraday_bars_1400.py
python scripts/build_intraday_snapshot_1400.py
python scripts/check_intraday_quality_1400.py
python scripts/build_intraday_manifest_1400.py
python scripts/build_intraday_ready_1400.py
python scripts/replay_intraday_1400_history.py
python scripts/build_t1_truth_vs_1400.py
python scripts/build_t1_intraday_trainset.py
python scripts/intraday_acceptance_check.py
python scripts/intraday_smoke_downstream_read.py
pytest
```

注意：

如果 Tushare token 或历史分钟权限不足，不要伪造成功。必须让盘中线 ready 输出 WARN 或 FAIL，并明确原因。

---

# 十八、最终验收标准

本次开发完成后，必须满足以下结果。

## 18.1 日线独立 PASS

存在：

```text
metadata/daily/daily_ready.json
```

并且：

```text
line = daily
status = PASS
can_run_daily_model = true
can_run_intraday_model = false
```

## 18.2 盘中线独立状态

存在：

```text
metadata/intraday/intraday_ready_1400.json
```

并且：

```text
line = intraday_1400
can_run_daily_model = false
can_run_intraday_model = true 或 false
can_generate_formal_signal = false
```

如果历史分钟不足 150 天：

```text
status = WARN 或 FAIL
reason 包含 insufficient_intraday_history
can_train_model = false
```

## 18.3 互不污染

必须证明：

1. 日线 PASS 不会让盘中线 PASS。
2. 盘中线 FAIL 不会让日线 FAIL。
3. 日线 workflow 不写 intraday。
4. 盘中线 workflow 不写 daily。
5. 盘中线不读取 data/processed/cnsv_1min.parquet。
6. CNSVdata 不输出任何 formal signal。

---

# 十九、Codex 最终回复要求

开发完成后，请回复以下内容：

1. 修改了哪些文件。
2. 日线数据线现在读取哪些路径。
3. 盘中线数据线现在读取哪些路径。
4. 是否已经删除盘中线 fallback 到 data/processed 的逻辑。
5. 日线 ready 文件路径。
6. 盘中线 ready 文件路径。
7. 日线验收结果。
8. 盘中线验收结果。
9. 如果盘中线 WARN / FAIL，具体原因是什么。
10. pytest 是否通过。
11. 是否确认 CNSVdata 仍然不生成任何预测、买卖建议、formal signal。

本次任务的最终目标不是让所有状态表面 PASS，而是让架构边界真实可靠：

日线归日线。  
盘中线归盘中线。  
两条数据线互不交叉，互不污染，互不影响。
