# CNSV 盘中线CNSV主程序需求.MD

版本：V1.0  
日期：2026-06-20  
项目名称：CNSV 盘中线  
适用仓库：CNSV  
仓库职责：主程序、特征、模型、预测、验证、机器学习、报告  
数据来源：CNSVdata 盘中线数据  
交易方式：人工决策、人工操作，不做自动交易  

---

## 0. 本文档定位

本文档定义 CNSV 主程序在《CNSV 盘中线》中的功能需求。

CNSV 主程序不负责采集原始数据。它只读取 CNSVdata 已经验收通过的 14:00 盘中快照、T+1 真值标签和训练样本底座。

CNSV 主程序负责：

1. 特征构建。
2. 模型训练。
3. T+1 涨跌概率预测。
4. T+1 涨跌幅预测。
5. T+1 价格区间预测。
6. 预测结果保存。
7. T+1 真值验证。
8. 机器学习更新。
9. 人工决策辅助报告。

---

## 1. 主程序总目标

在 T 日 14:00 后，CNSV 主程序读取 CNSVdata 的盘中快照，预测：

> T+1 收盘价相对于 T 日 14:00 价格的涨跌概率、涨跌幅度和价格区间。

并在 T+1 收盘后验证：

> 系统预测是否命中真实涨跌方向，预测涨跌幅误差是多少，价格区间是否覆盖真实收盘价。

---

## 2. 输入数据

CNSV 主程序必须从 CNSVdata 读取数据。

### 2.1 优先读取 ready 文件

必须先读取：

```text
metadata/intraday/intraday_ready_1400.json
```

读取规则：

1. ready = false：停止预测。
2. status = FAIL：停止预测。
3. status = WARN：允许低置信预测，但报告必须提示。
4. status = PASS：允许正常观察级预测。
5. allowed_usage.can_run_intraday_forecast = false：停止预测。
6. allowed_usage.can_generate_formal_signal 必须为 false。

---

### 2.2 盘中快照输入

读取：

```text
data/intraday/snapshots/YYYYMMDD/1400/
```

核心文件：

```text
cnsv_1min_asof_1400.parquet
cnsv_5min_asof_1400.parquet
cnsv_15min_asof_1400.parquet
intraday_snapshot_1400.json
intraday_quality_1400.json
intraday_manifest_1400.json
```

---

### 2.3 训练样本输入

读取：

```text
data/ml_dataset/t1_intraday/t1_intraday_trainset.parquet
```

---

### 2.4 真值标签输入

读取：

```text
data/labels/t1_truth/t1_truth_vs_1400_latest.parquet
```

---

## 3. 输出数据

CNSV 主程序新增输出目录：

```text
data/predictions/intraday_line/
data/validation/intraday_line/
data/model_registry/intraday_line/
reports/intraday_line/
models/intraday_line/
```

---

### 3.1 预测记录

文件：

```text
data/predictions/intraday_line/t1_intraday_predictions.parquet
data/predictions/intraday_line/t1_intraday_predictions_latest.csv
```

字段：

```text
trade_date
asof_time
ts_code
name
asof_price_1400
next_trade_date

pred_up_prob
pred_down_prob
pred_flat_prob
pred_return
pred_price_low
pred_price_mid
pred_price_high
interval_confidence

model_confidence
model_version
feature_version
trainset_version
training_sample_count

data_quality_status
risk_flags
manual_decision_reference
created_at
```

---

### 3.2 验证记录

文件：

```text
data/validation/intraday_line/t1_intraday_validation.parquet
data/validation/intraday_line/t1_intraday_validation_latest.csv
```

字段：

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

pred_up_prob
pred_down_prob
pred_flat_prob
pred_return
pred_price_low
pred_price_mid
pred_price_high

direction_hit
return_error
abs_return_error
squared_return_error
price_interval_hit
lower_breach
upper_breach

model_version
feature_version
validated_at
```

---

### 3.3 模型指标

文件：

```text
data/validation/intraday_line/intraday_model_metrics_latest.json
```

字段：

```text
model_version
feature_version
sample_count
validation_start_date
validation_end_date

direction_hit_rate
auc
brier_score
log_loss
precision_when_pred_up
recall_when_actual_up

mae
rmse
mean_error
median_error
spearman_ic
pearson_corr

price_interval_hit_rate
lower_breach_rate
upper_breach_rate
average_interval_width

calibration_buckets
created_at
```

---

### 3.4 报告输出

目录：

```text
reports/intraday_line/YYYYMMDD/
```

文件：

```text
cnsv_intraday_line_report_YYYYMMDD.md
cnsv_intraday_line_report_latest.md
```

---

## 4. 主程序模块设计

建议新增模块：

```text
src/cnsv/intraday_line/
```

文件：

```text
src/cnsv/intraday_line/io.py
src/cnsv/intraday_line/schema.py
src/cnsv/intraday_line/features.py
src/cnsv/intraday_line/models.py
src/cnsv/intraday_line/train.py
src/cnsv/intraday_line/predict.py
src/cnsv/intraday_line/validate.py
src/cnsv/intraday_line/calibration.py
src/cnsv/intraday_line/report.py
src/cnsv/intraday_line/model_registry.py
```

配置：

```text
config/intraday_line.yml
```

---

## 5. 模块职责

### 5.1 io.py

职责：

1. 读取 CNSVdata ready 文件。
2. 读取 1min / 5min / 15min 快照。
3. 读取 snapshot JSON。
4. 读取 quality JSON。
5. 读取训练样本。
6. 读取 T+1 真值。
7. 保存预测记录。
8. 保存验证记录。
9. 保存报告。

硬约束：

不得绕过 ready 文件直接读取 snapshots。

---

### 5.2 schema.py

职责：

1. 定义输入 schema。
2. 定义预测输出 schema。
3. 定义验证输出 schema。
4. 检查字段类型。
5. 检查关键字段缺失。

关键字段缺失时必须 FAIL。

---

### 5.3 features.py

职责：

基于 CNSVdata 14:00 快照构建模型特征。

特征必须只来自 T 日 14:00 及以前数据。

---

### 5.4 models.py

职责：

1. 定义方向分类模型。
2. 定义收益回归模型。
3. 定义价格区间模型。
4. 定义 ensemble 逻辑。
5. 定义 baseline fallback 逻辑。

---

### 5.5 train.py

职责：

1. 读取训练样本。
2. 做时间序列切分。
3. 训练模型。
4. 做 walk-forward 验证。
5. 生成模型指标。
6. 保存模型文件。
7. 更新 model registry。

---

### 5.6 predict.py

职责：

1. 读取当天 14:00 快照。
2. 构建特征。
3. 加载可用模型。
4. 输出 T+1 预测。
5. 保存 prediction record。
6. 生成当日报告。

---

### 5.7 validate.py

职责：

1. T+1 收盘后读取真值。
2. 匹配 T 日预测记录。
3. 计算 direction_hit。
4. 计算 return_error。
5. 计算 price_interval_hit。
6. 更新 validation 文件。
7. 更新模型指标。

---

### 5.8 calibration.py

职责：

1. 计算概率校准。
2. 输出分桶命中率。
3. 支持 Platt Scaling。
4. 支持 Isotonic Regression。
5. 当样本不足时自动回退到不校准或简单校准。

---

### 5.9 report.py

职责：

生成面向人工的尾盘决策辅助报告。

报告必须大白话可读，同时保留量化指标。

---

### 5.10 model_registry.py

职责：

1. 记录模型版本。
2. 记录训练窗口。
3. 记录训练样本数量。
4. 记录模型指标。
5. 支持新旧模型对比。
6. 支持模型回滚。
7. 禁止指标更差的新模型覆盖旧模型。

---

## 6. 特征工程需求

### 6.1 基础价量特征

必须支持：

```text
return_from_open_to_1400
return_from_vwap_to_1400
high_until_1400
low_until_1400
range_until_1400
close_position_until_1400
high_drawdown_until_1400
low_rebound_until_1400
intraday_volatility_until_1400
```

---

### 6.2 成交量/成交额特征

必须支持：

```text
volume_until_1400
amount_until_1400
morning_volume
afternoon_volume_until_1400
morning_amount
afternoon_amount_until_1400
afternoon_volume_ratio
afternoon_amount_ratio
volume_slope_afternoon
amount_slope_afternoon
```

---

### 6.3 趋势特征

必须支持：

```text
price_slope_morning
price_slope_afternoon
vwap_slope
last_30min_return
last_15min_return
last_5min_return
```

---

### 6.4 波动特征

必须支持：

```text
realized_volatility_until_1400
max_1min_return
min_1min_return
mean_abs_1min_return
volatility_last_30min
volatility_last_15min
```

---

### 6.5 风险特征

必须支持：

```text
intraday_pullback_ratio
intraday_chase_risk
upper_shadow_risk_until_1400
volume_price_divergence
late_session_weakness
data_delay_risk
```

---

### 6.6 扩展特征

后续可支持：

```text
market_index_return_until_1400
industry_index_return_until_1400
moneyflow_partial_signal
news_event_flag
volatility_regime
```

但扩展特征必须满足：

1. 14:00 前可见。
2. 有明确数据来源。
3. 有缺失处理。
4. 不得造成未来函数。

---

## 7. 预测任务定义

### 7.1 方向分类任务

目标：

```text
actual_up_label
```

输出：

```text
pred_up_prob
pred_down_prob
pred_flat_prob
```

其中：

```text
pred_up_prob + pred_down_prob + pred_flat_prob ≈ 1
```

如果暂不做 flat 三分类，可以先做二分类：

```text
pred_up_prob
pred_down_prob = 1 - pred_up_prob
```

---

### 7.2 收益回归任务

目标：

```text
actual_return_vs_1400
```

输出：

```text
pred_return
```

---

### 7.3 价格区间任务

目标：

预测 T+1 收盘价格区间。

输出：

```text
pred_price_low
pred_price_mid
pred_price_high
interval_confidence
```

计算逻辑：

```text
pred_price_mid = asof_price_1400 * (1 + pred_return)
```

low / high 可来自：

1. 历史误差分布。
2. 分位数回归。
3. 模型残差区间。
4. 波动率调整区间。

---

## 8. 模型路线

### 8.1 V1 baseline 模型

在样本较少时，必须先有 baseline。

baseline 可以包括：

1. 近 N 日平均收益。
2. 近 N 日上涨频率。
3. 当日 14:00 前涨跌幅分位。
4. 简单量价打分。
5. 线性模型。

baseline 的价值是防止机器学习样本不足时乱预测。

---

### 8.2 V2 机器学习模型

样本足够后启用：

1. Logistic Regression。
2. Ridge / Lasso。
3. Random Forest。
4. Gradient Boosting。
5. LightGBM / XGBoost，如环境允许。
6. Quantile Regression。
7. Ensemble。

---

### 8.3 Ensemble 规则

最终输出建议来自多个模型融合：

```text
pred_up_prob = weighted_average(classifier_probs)
pred_return = weighted_average(regression_preds)
price_interval = quantile_or_residual_interval
```

权重依据：

1. 最近 walk-forward 表现。
2. Brier Score。
3. MAE。
4. 稳定性。
5. 样本覆盖率。

---

## 9. 训练与回测要求

### 9.1 时间序列切分

禁止随机打乱样本做训练/测试。

必须使用：

```text
train: 早期日期
validation: 中间日期
test: 后期日期
```

或 walk-forward：

```text
用过去窗口训练，预测下一个窗口。
```

---

### 9.2 walk-forward 验证

必须支持：

1. rolling window。
2. expanding window。
3. 每个预测点只用历史样本训练。
4. 不允许未来样本进入训练。

---

### 9.3 最低样本阈值

建议：

```text
sample_count < 60：只允许 baseline
60 <= sample_count < 180：允许简单线性模型
sample_count >= 180：允许树模型
sample_count >= 360：允许 ensemble
```

阈值可配置，但不能没有阈值。

---

## 10. 概率校准要求

模型输出概率必须检查校准度。

必须支持：

1. Brier Score。
2. Calibration Buckets。
3. Reliability Curve 数据。
4. 预测概率分桶命中率。

分桶示例：

```text
0.50 - 0.55
0.55 - 0.60
0.60 - 0.65
0.65 - 0.70
0.70 - 0.80
0.80+
```

如果某个概率桶样本太少，报告必须提示不稳定。

---

## 11. 验证指标

### 11.1 单日验证

T+1 收盘后，每条预测必须生成：

```text
direction_hit
return_error
abs_return_error
price_interval_hit
```

---

### 11.2 总体指标

必须生成：

```text
direction_hit_rate
auc
brier_score
log_loss
mae
rmse
spearman_ic
pearson_corr
price_interval_hit_rate
calibration_bucket_accuracy
```

---

### 11.3 人工辅助指标

建议生成：

```text
high_confidence_count
high_confidence_hit_rate
warn_data_hit_rate
risk_flag_hit_rate
false_positive_cases
false_negative_cases
```

---

## 12. 报告需求

### 12.1 当日预测报告结构

报告文件：

```text
reports/intraday_line/YYYYMMDD/cnsv_intraday_line_report_YYYYMMDD.md
```

报告必须包含：

1. 项目名称。
2. 交易日。
3. asof_time。
4. asof_price_1400。
5. CNSVdata 数据状态。
6. T+1 预测日期。
7. 上涨概率。
8. 下跌概率。
9. 震荡概率。
10. 预期涨跌幅。
11. 价格区间。
12. 模型置信度。
13. 训练样本数量。
14. 模型版本。
15. 特征版本。
16. 主要风险标签。
17. 人工决策参考。
18. 近 N 次预测命中回顾。
19. 免责声明：非自动交易，不构成确定性结论。

---

### 12.2 报告表格字段

建议表格：

```text
日期｜14:00价格｜T+1预测日期｜上涨概率｜下跌概率｜预期涨跌幅｜预测价格区间｜模型置信度｜数据状态｜风险标签｜人工参考
```

---

### 12.3 人工参考输出规则

允许输出：

```text
观察
谨慎观察
风险偏高
禁止追高
低置信，仅记录
可进入人工观察池
```

谨慎输出：

```text
小仓试错参考
减仓观察参考
```

禁止输出：

```text
确定买入
确定卖出
满仓
梭哈
稳赚
明日必涨
明日必涨停
自动交易
```

---

## 13. 机器学习更新闭环

### 13.1 每日闭环

```text
T 日 14:00
    ↓
生成预测
    ↓
保存 prediction
    ↓
T+1 收盘后
    ↓
读取 truth
    ↓
生成 validation
    ↓
更新 metrics
    ↓
追加训练样本
    ↓
判断是否需要再训练
```

---

### 13.2 再训练触发条件

建议：

1. 每周固定再训练一次。
2. 新增样本 >= 20 条后再训练。
3. 连续预测误差异常时再训练。
4. 模型校准明显失效时再训练。
5. 手动 workflow_dispatch 触发再训练。

---

### 13.3 模型替换规则

新模型不能直接覆盖旧模型。

只有满足以下条件才允许替换：

1. walk-forward 指标不差于旧模型。
2. Brier Score 不恶化。
3. MAE 不恶化。
4. 方向命中率不明显下降。
5. 价格区间命中率不明显下降。
6. 样本量足够。
7. model_registry 记录完整。

否则新模型只能保存为 candidate，不能设为 active。

---

## 14. 风控与置信度

### 14.1 模型置信度

model_confidence 不等于 pred_up_prob。

model_confidence 应综合：

1. 数据质量。
2. 训练样本数量。
3. 模型最近表现。
4. 概率校准情况。
5. 当前特征是否落在历史常见分布内。
6. 多模型是否一致。
7. 价格波动是否异常。

可分为：

```text
HIGH
MEDIUM
LOW
INVALID
```

---

### 14.2 风险标签

建议支持：

```text
DATA_WARN
LOW_SAMPLE
MODEL_UNCALIBRATED
FEATURE_OUT_OF_DISTRIBUTION
INTRADAY_PULLBACK
CHASE_RISK
VOLUME_PRICE_DIVERGENCE
HIGH_VOLATILITY
LOW_LIQUIDITY
MONEYFLOW_DELAY
```

---

## 15. 防未来函数硬约束

CNSV 主程序必须防止以下错误：

1. 预测 T 日时使用 T 日收盘价。
2. 预测 T 日时使用 T+1 收盘价。
3. 训练历史模型时把未来样本混进训练集。
4. 特征工程使用 14:00 之后分钟数据。
5. 用全样本归一化后再回测。
6. 用全样本选择特征后再做历史回测。
7. 用未来验证结果调模型再回填历史预测。
8. 使用文件修改时间作为特征。
9. 使用未来 corporate action 信息影响历史 T 日特征。
10. 预测报告生成后被验证流程覆盖原预测值。

任何防未来函数测试不通过，当前版本必须 FAIL。

---

## 16. GitHub Actions 工作流需求

建议新增：

```text
.github/workflows/run_intraday_line_predict.yml
.github/workflows/run_intraday_line_validate.yml
.github/workflows/run_intraday_line_train.yml
```

---

### 16.1 run_intraday_line_predict.yml

运行时间：

```text
14:10 BJT / 06:10 UTC
```

流程：

```text
pip install -r requirements.txt
python -m cnsv.intraday_line.predict
python -m cnsv.intraday_line.report
pytest
```

---

### 16.2 run_intraday_line_validate.yml

运行时间：

```text
T+1 收盘数据更新后
建议 18:40 BJT / 10:40 UTC
```

流程：

```text
python -m cnsv.intraday_line.validate
python -m cnsv.intraday_line.report --validation
pytest
```

---

### 16.3 run_intraday_line_train.yml

触发：

1. workflow_dispatch。
2. 每周定时。
3. validation 后满足再训练条件。

流程：

```text
python -m cnsv.intraday_line.train
python -m cnsv.intraday_line.calibration
python -m cnsv.intraday_line.model_registry
pytest
```

---

## 17. 配置文件需求

配置文件：

```text
config/intraday_line.yml
```

建议内容：

```text
project_name: CNSV 盘中线
target:
  ts_code: 600150.SH
  name: 中国船舶

asof:
  time: "14:00"
  timezone: Asia/Shanghai
  windows:
    - ["09:30", "11:30"]
    - ["13:00", "14:00"]

truth:
  target: t1_close_vs_t_1400
  flat_threshold: 0.002

data_contract:
  ready_file: metadata/intraday/intraday_ready_1400.json
  snapshot_dir_template: data/intraday/snapshots/{trade_date}/1400/

model:
  min_samples_baseline: 60
  min_samples_ml: 180
  active_model_policy: best_validated
  calibration: true

report:
  output_dir: reports/intraday_line/
  include_recent_validation_count: 20
```

---

## 18. 测试需求

新增测试：

```text
tests/intraday_line/test_io_ready_gate.py
tests/intraday_line/test_schema.py
tests/intraday_line/test_features_no_future.py
tests/intraday_line/test_predict_output_schema.py
tests/intraday_line/test_validate_metrics.py
tests/intraday_line/test_train_walk_forward.py
tests/intraday_line/test_calibration.py
tests/intraday_line/test_report.py
tests/intraday_line/test_model_registry.py
```

---

### 18.1 必测项

1. ready=false 时不得预测。
2. status=FAIL 时不得预测。
3. status=WARN 时报告必须降置信。
4. 特征不得包含 14:00 后数据。
5. 输出字段完整。
6. pred_up_prob 在 0 到 1 之间。
7. pred_down_prob 在 0 到 1 之间。
8. pred_price_low <= pred_price_mid <= pred_price_high。
9. validation 能正确计算 direction_hit。
10. validation 能正确计算 return_error。
11. walk-forward 不使用未来样本。
12. 新模型指标差时不能覆盖 active model。
13. 报告不输出确定性交易指令。

---

## 19. 阶段性交付

### V1.1 接线版

目标：

1. 读取 CNSVdata 14:00 ready。
2. 读取盘中快照。
3. 构建基础特征。
4. 使用 baseline 输出预测。
5. 生成当日报告。

---

### V1.2 验证版

目标：

1. 读取 T+1 truth。
2. 匹配历史预测。
3. 生成 validation。
4. 输出命中率和误差。
5. 报告中增加近 N 次预测回顾。

---

### V1.3 机器学习版

目标：

1. 读取训练样本。
2. 训练方向模型。
3. 训练收益模型。
4. 输出模型指标。
5. 支持模型版本管理。

---

### V1.4 校准与区间版

目标：

1. 概率校准。
2. 价格区间预测。
3. 区间命中率验证。
4. 风险标签系统。

---

### V2.0 人工决策辅助版

目标：

1. 预测链路稳定。
2. 验证链路稳定。
3. 机器学习闭环稳定。
4. 报告可直接辅助用户尾盘人工判断。
5. 仍然不自动交易。

---

## 20. Codex 开发要求

Codex 在 CNSV 主程序仓库开发时必须遵守：

1. 新增 intraday_line 独立模块，不要打乱现有 CNSV 主线。
2. 所有输入必须来自 CNSVdata 的正式契约文件。
3. 必须先读 ready，再读快照。
4. 不得绕过 ready。
5. 不得使用未来数据。
6. 不得自动交易。
7. 不得输出确定性买卖指令。
8. 所有预测必须保存 prediction record。
9. 所有真值回来后必须能 validation。
10. 所有模型必须有 model_version。
11. 所有特征必须有 feature_version。
12. 所有报告必须含数据状态和模型置信度。
13. pytest 必须覆盖 ready、schema、no future leak、predict、validate、report。
14. 如果数据不足，必须自动回退 baseline。
15. 如果模型效果不稳定，必须降低置信度，而不是强行给高置信结论。

---

## 21. 最终交付结果

CNSV 主程序在《CNSV 盘中线》中最终应交付：

```text
一个读取 CNSVdata 14:00 快照、预测 T+1 收盘相对 14:00 价格涨跌、自动验证命中、持续机器学习更新、并输出人工尾盘决策辅助报告的专业级主程序。
```

它回答：

1. 明天相对今天 14:00 价格，上涨概率是多少？
2. 下跌概率是多少？
3. 预期涨跌幅是多少？
4. 价格区间是多少？
5. 这次预测置信度如何？
6. 历史类似预测命中率如何？
7. 主要风险在哪里？
8. 是否值得进入人工观察池？

它不做：

1. 自动买入。
2. 自动卖出。
3. 确定性承诺。
4. 绕过验证的模型更新。
5. 使用未来数据的假回测。

最终目标是：

> 让用户在尾盘人工决策时，不再只靠主观感觉，而是有一套可验证、可回测、可进化的盘中量化辅助系统。
