# CNSV 盘中线CNSVdata数据需求.MD

版本：V1.0  
日期：2026-06-20  
项目名称：CNSV 盘中线  
适用仓库：CNSVdata  
仓库职责：只放数据，只做盘中快照、真值标签、训练样本底座、质量检查和下游读取契约  
禁止事项：不预测、不出交易建议、不生成买卖信号  

---

## 0. 本文档定位

本文档定义 CNSVdata 仓库在《CNSV 盘中线》中的数据层需求。

CNSVdata 是上游数据仓库，负责把 T 日 14:00 以前真实可见的数据整理成可靠、可追溯、可验收的盘中快照，并在 T+1 收盘后生成真实结果标签。

CNSVdata 不承担预测职责。预测、模型、机器学习和人工决策辅助报告全部由 CNSV 主程序完成。

---

## 1. 数据层总目标

CNSVdata 需要新增一条独立的盘中数据线：

```text
09:30 - 11:30
13:00 - 14:00
截至 14:00 生成盘中快照
```

并支持：

1. 真实盘中运行快照。
2. 历史 14:00 快照重放。
3. T+1 真值标签生成。
4. 中性机器学习训练样本底座生成。
5. 质量检查。
6. manifest / lineage / ready 下游读取契约。
7. 人工 CSV 预览文件。

---

## 2. 数据边界

### 2.1 允许 CNSVdata 生成的数据

允许生成：

1. 1min 盘中数据。
2. 5min 盘中聚合数据。
3. 15min 盘中聚合数据。
4. 14:00 快照 JSON。
5. 14:00 质量报告。
6. 14:00 ready 开关。
7. T+1 收盘真值标签。
8. 训练样本底座。
9. 历史重放快照。
10. CSV 预览文件。

---

### 2.2 禁止 CNSVdata 生成的内容

禁止生成：

1. pred_up_prob。
2. pred_down_prob。
3. pred_return。
4. pred_price_low / mid / high。
5. 模型置信度。
6. 买入建议。
7. 卖出建议。
8. 尾盘操作结论。
9. 涨停预测结论。
10. 任何 formal signal。

CNSVdata 的 allowed_usage.can_generate_formal_signal 必须始终为 false。

---

## 3. 核心目录设计

新增目录如下：

```text
data/intraday/snapshots/YYYYMMDD/1400/
data/intraday/replay/YYYYMMDD/1400/
data/labels/t1_truth/
data/ml_dataset/t1_intraday/
data/preview/intraday/
data/quality/intraday/
metadata/intraday/
```

---

### 3.1 snapshots 目录

真实盘中运行产生的快照存放于：

```text
data/intraday/snapshots/YYYYMMDD/1400/
```

示例：

```text
data/intraday/snapshots/20260622/1400/
    cnsv_1min_asof_1400.parquet
    cnsv_5min_asof_1400.parquet
    cnsv_15min_asof_1400.parquet
    intraday_snapshot_1400.json
    intraday_quality_1400.json
    intraday_manifest_1400.json
    intraday_ready_1400.json
```

---

### 3.2 replay 目录

历史重放快照存放于：

```text
data/intraday/replay/YYYYMMDD/1400/
```

用途：

1. 用历史分钟线模拟过去每个交易日 14:00 时系统能看到什么。
2. 生成机器学习训练样本。
3. 防止只有少量真实盘中样本导致模型无法训练。

历史重放不得使用 T 日 14:00 之后的数据生成 T 日特征。

---

### 3.3 labels 目录

T+1 真值标签存放于：

```text
data/labels/t1_truth/
```

建议文件：

```text
t1_truth_vs_1400_latest.parquet
t1_truth_vs_1400_latest.csv
t1_truth_manifest.json
t1_truth_quality.json
```

---

### 3.4 ml_dataset 目录

训练样本底座存放于：

```text
data/ml_dataset/t1_intraday/
```

建议文件：

```text
t1_intraday_trainset.parquet
t1_intraday_trainset_latest.csv
feature_manifest.json
label_manifest.json
trainset_quality.json
```

说明：

CNSVdata 只生成中性训练样本底座，不训练模型，不输出预测。

---

### 3.5 metadata 目录

盘中线元数据存放于：

```text
metadata/intraday/
```

建议文件：

```text
intraday_latest_trade_date.json
intraday_latest_snapshot.json
intraday_ready_1400.json
intraday_lineage_latest.json
intraday_downstream_contract.json
```

---

### 3.6 quality 目录

盘中质量检查结果存放于：

```text
data/quality/intraday/
```

建议文件：

```text
intraday_quality_latest.json
intraday_gaps_latest.json
intraday_acceptance_latest.json
intraday_failure_summary_latest.md
```

---

## 4. 核心脚本设计

新增脚本建议如下：

```text
scripts/fetch_intraday_1min_1400.py
scripts/build_intraday_snapshot_1400.py
scripts/build_intraday_bars_1400.py
scripts/check_intraday_quality_1400.py
scripts/build_intraday_manifest_1400.py
scripts/build_intraday_ready_1400.py
scripts/build_t1_truth_vs_1400.py
scripts/replay_intraday_1400_history.py
scripts/build_t1_intraday_trainset.py
scripts/build_intraday_preview_csv.py
scripts/intraday_acceptance_check.py
scripts/intraday_smoke_downstream_read.py
```

---

## 5. 脚本职责

### 5.1 fetch_intraday_1min_1400.py

职责：

1. 拉取 T 日 1min 数据。
2. 只保留 09:30 - 11:30、13:00 - 14:00。
3. 不拉取或不写入 14:00 之后数据。
4. 输出原始盘中 1min 快照。

输出：

```text
data/intraday/snapshots/YYYYMMDD/1400/cnsv_1min_asof_1400.parquet
```

---

### 5.2 build_intraday_bars_1400.py

职责：

1. 基于 1min 快照生成 5min bar。
2. 基于 1min 快照生成 15min bar。
3. 聚合不得跨午休时间错误合并。
4. 聚合必须只使用 14:00 及以前数据。

输出：

```text
cnsv_5min_asof_1400.parquet
cnsv_15min_asof_1400.parquet
```

---

### 5.3 build_intraday_snapshot_1400.py

职责：

生成快照摘要。

输出：

```text
intraday_snapshot_1400.json
```

核心内容：

```text
trade_date
ts_code
name
asof_time
asof_price_1400
last_valid_trade_time
open_0930
high_until_1400
low_until_1400
close_asof_1400
vwap_until_1400
volume_until_1400
amount_until_1400
return_from_open_to_1400
return_from_vwap_to_1400
high_drawdown_until_1400
low_rebound_until_1400
morning_volume
afternoon_volume_until_1400
morning_amount
afternoon_amount_until_1400
minute_count_expected
minute_count_actual
missing_minute_count
created_at
source
```

---

### 5.4 check_intraday_quality_1400.py

职责：

检查盘中快照质量。

检查项：

1. 是否交易日。
2. 是否存在 14:00 以前数据。
3. 是否覆盖上午窗口。
4. 是否覆盖下午窗口。
5. 是否缺分钟。
6. 是否重复分钟。
7. 是否价格为 0 或负数。
8. 是否成交量为负数。
9. 是否 high < low。
10. 是否 open / close 超出 high / low。
11. 是否最后有效分钟早于 13:55。
12. 是否出现异常跳价。
13. 是否数据源返回延迟。
14. 是否 parquet 可读。
15. 是否 schema 完整。

输出：

```text
intraday_quality_1400.json
```

---

### 5.5 build_intraday_ready_1400.py

职责：

生成 CNSV 主程序读取盘中数据前必须检查的 ready 文件。

输出：

```text
metadata/intraday/intraday_ready_1400.json
```

字段建议：

```text
{
  "project": "CNSV 盘中线",
  "repo": "CNSVdata",
  "trade_date": "YYYYMMDD",
  "asof_time": "14:00",
  "ready": true,
  "status": "PASS",
  "reason": [],
  "latest_snapshot_path": "data/intraday/snapshots/YYYYMMDD/1400/",
  "quality_path": "data/intraday/snapshots/YYYYMMDD/1400/intraday_quality_1400.json",
  "allowed_usage": {
    "can_develop_cnsv_main_program": true,
    "can_run_intraday_forecast": true,
    "can_run_backtest": false,
    "can_train_model": false,
    "can_generate_formal_signal": false
  },
  "created_at": "ISO8601"
}
```

---

## 6. 盘中 ready 状态规则

### 6.1 PASS

满足以下条件可为 PASS：

1. 当前日期为 A 股交易日。
2. 1min 数据覆盖主要窗口。
3. asof_price_1400 有效。
4. 最后一条有效分钟 >= 13:59 或等于 14:00。
5. 缺分钟数量在允许阈值内。
6. 无关键 schema 缺失。
7. 无价格逻辑错误。
8. parquet 可读。
9. manifest 可读。
10. quality 检查无 FAIL。

---

### 6.2 WARN

以下情况为 WARN：

1. 有少量非关键分钟缺失。
2. 数据源延迟但最后有效分钟 >= 13:55。
3. 成交额字段缺失但可从 price * volume 近似派生。
4. moneyflow 不可用，但盘中价量数据完整。
5. 5min / 15min 聚合存在非关键缺口，但 1min 主数据可用。
6. 历史参考缺口不影响当前 14:00 快照。

WARN 时允许 CNSV 主程序生成低置信预测，但必须在报告中提示数据风险。

---

### 6.3 FAIL

以下情况必须 FAIL：

1. 非交易日却生成交易快照。
2. 1min 文件缺失。
3. asof_price_1400 缺失。
4. 最后一条有效分钟早于 13:55。
5. 上午或下午核心窗口完全缺失。
6. 关键字段缺失。
7. parquet 不可读。
8. 时间戳无法解析。
9. 出现明显价格非法值。
10. 质量检查脚本异常退出。
11. manifest 缺失。
12. ready 文件生成失败。

FAIL 时 CNSV 主程序不得读取该快照生成预测。

---

## 7. 盘中 1min 数据 schema

文件：

```text
cnsv_1min_asof_1400.parquet
```

字段：

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
```

可选字段：

```text
pre_close
avg_price
vwap_cum
ret_from_open
ret_from_prev_min
bar_index
session
```

字段说明：

1. trade_date：交易日，格式 YYYYMMDD。
2. trade_time：分钟时间戳。
3. session：morning 或 afternoon。
4. bar_index：盘中 bar 序号。
5. close：该分钟收盘价。
6. volume：该分钟成交量。
7. amount：该分钟成交额。

---

## 8. 5min / 15min 聚合 schema

文件：

```text
cnsv_5min_asof_1400.parquet
cnsv_15min_asof_1400.parquet
```

字段：

```text
trade_date
bar_start_time
bar_end_time
ts_code
open
high
low
close
volume
amount
vwap
bar_freq
source_1min_count
expected_1min_count
missing_1min_count
session
created_at
```

聚合规则：

1. open = 窗口第一条 1min open。
2. high = 窗口内最高 high。
3. low = 窗口内最低 low。
4. close = 窗口最后一条 1min close。
5. volume = 窗口成交量加总。
6. amount = 窗口成交额加总。
7. vwap = amount / volume，注意单位一致。
8. 不得把上午 11:30 和下午 13:00 错误聚合在同一个 bar 内。

---

## 9. T+1 真值标签需求

### 9.1 真值生成时间

T+1 收盘后生成。建议在 CNSVdata 日线数据更新完成之后运行。

---

### 9.2 真值文件

```text
data/labels/t1_truth/t1_truth_vs_1400_latest.parquet
data/labels/t1_truth/t1_truth_vs_1400_latest.csv
```

---

### 9.3 真值 schema

```text
trade_date
asof_time
ts_code
asof_price_1400
next_trade_date
next_close
actual_return_vs_1400
actual_up_label
actual_down_label
actual_flat_label
actual_limitup_label
truth_ready
truth_status
created_at
```

---

### 9.4 真值口径

```text
actual_return_vs_1400 = next_close / asof_price_1400 - 1
```

标签：

```text
actual_up_label = 1 if actual_return_vs_1400 > 0 else 0
actual_down_label = 1 if actual_return_vs_1400 < 0 else 0
actual_flat_label = 1 if abs(actual_return_vs_1400) <= 0.002 else 0
```

actual_limitup_label 可作为扩展字段，用于未来判断次日是否涨停。

---

## 10. 历史 14:00 快照重放需求

### 10.1 为什么必须做历史重放

如果只从当前日期开始每天积累一个样本，机器学习样本太少，模型无法可靠训练。

因此 CNSVdata 必须支持：

```text
用历史 1min 数据，重放每个历史交易日 14:00 时系统能看到的数据。
```

---

### 10.2 重放规则

对每个历史交易日：

1. 只截取 09:30 - 11:30、13:00 - 14:00。
2. 生成 asof_price_1400。
3. 生成 1min / 5min / 15min 快照。
4. 生成 T+1 真值。
5. 生成训练样本。
6. 标记 replay = true。
7. 不允许使用 14:00 之后数据构造 T 日特征。

---

### 10.3 重放输出

```text
data/intraday/replay/YYYYMMDD/1400/
    cnsv_1min_asof_1400.parquet
    cnsv_5min_asof_1400.parquet
    cnsv_15min_asof_1400.parquet
    intraday_snapshot_1400.json
    intraday_quality_1400.json
    intraday_manifest_1400.json
```

---

## 11. 训练样本底座需求

文件：

```text
data/ml_dataset/t1_intraday/t1_intraday_trainset.parquet
```

### 11.1 schema

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

data_quality_status
snapshot_type
feature_version
label_version
created_at
```

---

### 11.2 feature_version

训练样本必须有 feature_version。

示例：

```text
feature_version = "intraday_1400_v1"
```

后续新增特征时必须升级版本，不能静默覆盖。

---

### 11.3 label_version

标签必须有 label_version。

示例：

```text
label_version = "t1_close_vs_1400_v1"
```

如果未来真值口径改变，必须升级 label_version。

---

## 12. 防未来函数检查

CNSVdata 必须新增防未来函数检查。

检查项：

1. 训练样本中的特征时间不得晚于 T 日 14:00。
2. T 日 close 不得进入特征。
3. T+1 close 只能进入 label，不得进入 feature。
4. replay 快照不得包含 14:00 后的 1min bar。
5. trainset 中 feature 字段不得由 label 字段派生。
6. 文件 created_at 不得作为模型特征。
7. 未来 corporate action 信息不得影响历史 T 日特征。
8. 如果数据中存在未来信息泄露风险，trainset_quality 必须 FAIL。

---

## 13. GitHub Actions 工作流需求

建议新增 workflows：

```text
.github/workflows/fetch_intraday_1400.yml
.github/workflows/build_t1_truth.yml
.github/workflows/build_intraday_trainset.yml
.github/workflows/intraday_acceptance.yml
```

---

### 13.1 fetch_intraday_1400.yml

用途：

1. 盘中 14:00 后运行。
2. 支持手动 workflow_dispatch。
3. 支持定时运行。

建议时间：

```text
14:05 BJT / 06:05 UTC
```

流程：

```text
pip install -r requirements.txt
python scripts/fetch_intraday_1min_1400.py
python scripts/build_intraday_bars_1400.py
python scripts/build_intraday_snapshot_1400.py
python scripts/check_intraday_quality_1400.py
python scripts/build_intraday_manifest_1400.py
python scripts/build_intraday_ready_1400.py
python scripts/build_intraday_preview_csv.py
pytest
```

---

### 13.2 build_t1_truth.yml

用途：

T+1 收盘后生成真值标签。

建议时间：

```text
18:30 BJT / 10:30 UTC
```

流程：

```text
python scripts/build_t1_truth_vs_1400.py
python scripts/build_t1_intraday_trainset.py
python scripts/build_intraday_preview_csv.py
python scripts/intraday_acceptance_check.py
```

---

### 13.3 build_intraday_trainset.yml

用途：

定期构建或刷新训练样本底座。

触发方式：

1. workflow_dispatch。
2. 每周定时。
3. T+1 truth 生成后可调用。

---

### 13.4 intraday_acceptance.yml

用途：

盘中线专用验收。

流程：

```text
pytest
python scripts/check_intraday_quality_1400.py
python scripts/intraday_acceptance_check.py
python scripts/intraday_smoke_downstream_read.py
python scripts/build_intraday_ready_1400.py
```

---

## 14. 人工预览 CSV 需求

GitHub 网页不方便查看 parquet，所以必须提供 CSV preview。

目录：

```text
data/preview/intraday/
```

文件：

```text
intraday_1min_1400_latest.csv
intraday_5min_1400_latest.csv
intraday_15min_1400_latest.csv
intraday_snapshot_1400_latest.csv
t1_truth_vs_1400_latest.csv
t1_intraday_trainset_latest.csv
intraday_preview_manifest.csv
```

CSV 只用于人工检查，不作为 CNSV 主程序正式读取源。

---

## 15. 下游读取契约

CNSV 主程序必须优先读取：

```text
metadata/intraday/intraday_ready_1400.json
```

然后再读取：

```text
data/intraday/snapshots/YYYYMMDD/1400/
```

如果 ready = false 或 status = FAIL，则 CNSV 主程序必须停止预测。

CNSV 主程序不得直接扫描 snapshots 目录绕过 ready。

---

## 16. 测试需求

新增测试目录建议：

```text
tests/test_intraday_snapshot_1400.py
tests/test_intraday_quality_1400.py
tests/test_t1_truth_vs_1400.py
tests/test_intraday_trainset.py
tests/test_intraday_no_future_leak.py
tests/test_intraday_ready_contract.py
tests/test_intraday_smoke_read.py
```

---

### 16.1 必测项

1. 非交易日不生成 PASS 快照。
2. 缺少 14:00 价格时 FAIL。
3. 最后分钟早于 13:55 时 FAIL。
4. 少量缺分钟时 WARN。
5. parquet schema 缺字段时 FAIL。
6. T+1 真值计算正确。
7. trainset 中 feature 不包含未来数据。
8. intraday_ready_1400.json 可被下游读取。
9. can_generate_formal_signal 永远为 false。
10. replay 只使用 14:00 以前数据。

---

## 17. 验收标准

CNSVdata V1.0/V1.1 完成后，必须满足：

1. 手动运行可生成 14:00 快照。
2. 快照目录结构正确。
3. 1min / 5min / 15min 文件可读。
4. asof_price_1400 正确。
5. quality JSON 正确。
6. ready JSON 正确。
7. preview CSV 正确。
8. 不污染现有 data/processed 主线。
9. 不生成任何预测字段。
10. pytest 全部通过。

CNSVdata V1.2 完成后，必须满足：

1. 能生成 T+1 真值。
2. actual_return_vs_1400 计算正确。
3. 标签字段正确。
4. truth_ready 正确。
5. 能被 CNSV 主程序读取。

CNSVdata V1.3 完成后，必须满足：

1. 能历史重放 14:00 快照。
2. 能生成训练样本底座。
3. 能防未来函数。
4. 能输出 feature_manifest 和 label_manifest。
5. 能支撑 CNSV 主程序训练模型。

---

## 18. Codex 开发要求

Codex 在 CNSVdata 仓库开发时必须遵守：

1. 只新增盘中线，不推翻现有 V1.2 数据主线。
2. 不修改 processed 文件含义。
3. 不把盘中数据写入正式收盘后 processed 主线。
4. 所有新增数据进入 data/intraday、data/labels、data/ml_dataset、metadata/intraday、data/quality/intraday。
5. 所有新增脚本必须可单独运行。
6. 所有新增 workflow 必须支持 workflow_dispatch。
7. 所有新增输出必须有 schema、manifest、quality、ready。
8. 所有异常必须明确 FAIL / WARN，不允许静默吞错。
9. TUSHARE_TOKEN 只能从环境变量读取。
10. 不得把 Token 写入代码、日志、JSON、CSV、Parquet 元数据。
11. 不得生成买卖建议。
12. 不得生成预测概率。
13. 不得生成 formal signal。
14. 完成后必须给出自检说明。

---

## 19. 最终交付结果

CNSVdata 在《CNSV 盘中线》中最终应交付：

```text
一条独立、干净、可追溯、可验收、可给 CNSV 主程序读取的 14:00 盘中数据线。
```

它只回答：

1. 今天 14:00 以前的数据是否完整？
2. 14:00 价格是多少？
3. 盘中量价状态是什么？
4. T+1 真实结果是什么？
5. 能不能作为训练样本？
6. 能不能给 CNSV 主程序读取？

它不回答：

1. 明天涨不涨？
2. 明天涨多少？
3. 要不要买？
4. 要不要卖？
5. 是否能涨停？

这些问题全部交给 CNSV 主程序。
