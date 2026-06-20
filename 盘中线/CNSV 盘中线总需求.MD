# CNSV 盘中线总需求.MD

版本：V1.0  
日期：2026-06-20  
项目名称：CNSV 盘中线  
适用仓库：CNSVdata + CNSV  
项目性质：A 股盘中 14:00 快照驱动的次交易日涨跌预测与人工决策辅助系统  
标的主线：600150.SH / 中国船舶  
交易方式：人工决策、人工下单，不做自动交易  

---

## 0. 总结一句话

《CNSV 盘中线》是一条独立于收盘后日线系统之外的盘中量化分支线：

> CNSVdata 仓库只负责在 A 股盘中生成截至 14:00 的独立数据快照、真值标签和训练样本底座；  
> CNSV 主程序读取该盘中快照，预测次交易日相对于 T 日 14:00 价格的涨跌概率、涨跌幅度和价格区间；  
> T+1 收盘后用真实市场结果验证预测是否命中，并把结果回写机器学习训练集；  
> 用户只把系统输出作为尾盘人工决策参考，不做自动交易。

---

## 1. 项目背景

当前 CNSVdata 已经具备分钟线、日线、资金流、数据质量检查、验收开关、下游读取契约等上游数据底座能力。

但现有 CNSVdata 主线主要面向收盘后数据闭环，不适合直接承担“盘中 14:00 预测次交易日涨跌”的任务。

《CNSV 盘中线》要解决的问题是：

1. 在 A 股尚未收盘前，形成独立的 14:00 数据快照。
2. 只使用 14:00 以前真实可见的数据，不偷看收盘后数据。
3. 用 CNSV 主程序预测 T+1 收盘相对 T 日 14:00 价格的涨跌概率、涨跌幅度和价格区间。
4. T+1 收盘后自动生成真实标签，验证预测是否命中。
5. 将预测与真实结果回写机器学习样本集，使模型具备持续校准和进化能力。
6. 最终输出给用户的是“尾盘人工决策辅助”，不是自动买卖指令。

---

## 2. 总目标

### 2.1 系统目标

建设一套可持续运行、可验证、可回测、可机器学习迭代的盘中 14:00 T+1 预测系统。

核心问题：

> 在 T 日 14:00 时，基于 09:30 - 11:30、13:00 - 14:00 的盘中数据，预测 T+1 收盘价相对于 T 日 14:00 价格的涨跌概率、涨跌幅度和价格区间。

---

### 2.2 决策目标

系统不代替用户交易，只回答以下问题：

1. 明天相对于今天 14:00 价格，大概率上涨还是下跌？
2. 上涨概率是多少？
3. 下跌概率是多少？
4. 预期涨跌幅是多少？
5. 明天合理价格区间是多少？
6. 当前模型置信度是否足够？
7. 这次预测是否适合进入人工观察池？
8. 风险主要来自哪里？

---

## 3. 仓库职责边界

本项目必须严格拆分两个仓库职责。

---

### 3.1 CNSVdata 仓库职责

CNSVdata 只负责数据，不负责预测。

允许做：

1. 盘中分钟数据采集。
2. 盘中 14:00 快照生成。
3. 盘中快照质量检查。
4. 盘中快照 manifest / lineage / ready 开关。
5. T+1 市场真值标签生成。
6. 历史 14:00 快照重放。
7. 中性机器学习训练样本底座生成。
8. CSV 人工预览文件生成。
9. 给 CNSV 主程序提供数据读取契约。

禁止做：

1. 不生成买卖信号。
2. 不输出交易建议。
3. 不预测涨跌概率。
4. 不预测涨跌幅度。
5. 不输出尾盘买入/卖出结论。
6. 不把 14:00 盘中数据伪装成收盘后完整数据。
7. 不修改现有收盘后 processed 主线的含义。

CNSVdata 的核心定位：

> 数据底座 + 快照层 + 真值标签层 + 训练样本底座。

---

### 3.2 CNSV 主程序职责

CNSV 主程序负责模型、预测、验证和报告。

允许做：

1. 读取 CNSVdata 的 14:00 盘中快照。
2. 读取 CNSVdata 的 T+1 真值标签。
3. 构建模型特征。
4. 训练机器学习模型。
5. 输出 T+1 上涨概率、下跌概率、预期涨跌幅和价格区间。
6. 生成预测记录。
7. T+1 收盘后验证预测是否命中。
8. 计算 AUC、Brier、MAE、RMSE、Spearman IC、区间命中率等指标。
9. 生成尾盘人工决策辅助报告。
10. 维护模型版本、特征版本、训练样本版本和回测记录。

禁止做：

1. 不自动下单。
2. 不接券商交易接口。
3. 不在数据未 ready 时强行预测。
4. 不使用 14:00 之后的数据参与 14:00 预测。
5. 不使用 T+1 结果参与 T 日预测。
6. 不绕过 CNSVdata 的 ready 开关。
7. 不把观察级输出包装成确定性交易结论。

CNSV 主程序的核心定位：

> 预测引擎 + 机器学习闭环 + 验证系统 + 人工决策辅助报告。

---

## 4. 核心时间定义

### 4.1 T 日

T 日指当前分析日，即用户在 A 股盘中 14:00 准备做尾盘人工决策的交易日。

---

### 4.2 盘中采样窗口

本项目固定使用以下窗口：

1. 上午：09:30 - 11:30
2. 下午：13:00 - 14:00

合并窗口：

> 09:30 - 11:30 + 13:00 - 14:00

按 1 分钟 bar 口径，预期约 180 根 1min bar。实际根数以数据源时间戳规则为准，但必须在质量检查中显式记录 expected_count、actual_count、missing_minutes。

---

### 4.3 asof_time

本项目固定 asof_time：

> 14:00:00

所有 T 日预测只能使用 14:00 及以前可见数据。

---

### 4.4 asof_price_1400

T 日 14:00 价格定义：

优先使用：

> T 日 14:00 这一分钟 bar 的 close 价格。

如果数据源没有精确 14:00 bar，则使用：

> trade_time <= 14:00 的最后一条有效 close 价格。

但如果最后一条有效分钟数据早于 13:55，则判定为数据延迟或数据不完整，intraday_ready 必须降级为 WARN 或 FAIL。

---

### 4.5 T+1 真值口径

本项目最核心的真值口径：

> T+1 交易日收盘价，相对于 T 日 14:00 价格的涨跌。

真实收益率：

```text
actual_return_vs_1400 = next_close / asof_price_1400 - 1
```

上涨标签：

```text
actual_up_label = 1 if actual_return_vs_1400 > 0 else 0
```

下跌标签：

```text
actual_down_label = 1 if actual_return_vs_1400 < 0 else 0
```

震荡标签可选：

```text
actual_flat_label = 1 if abs(actual_return_vs_1400) <= flat_threshold else 0
```

默认 flat_threshold 建议为 0.002，即 ±0.20%。

---

## 5. 总体流程

### 5.1 T 日 14:00 盘中快照流程

```text
T 日 14:00
    ↓
CNSVdata 拉取 09:30 - 11:30、13:00 - 14:00 盘中分钟数据
    ↓
生成 1min / 5min / 15min 盘中快照
    ↓
生成 intraday_quality_1400.json
    ↓
生成 intraday_ready_1400.json
    ↓
CNSV 主程序读取快照
    ↓
生成 T+1 预测
    ↓
输出尾盘人工决策辅助报告
```

---

### 5.2 T+1 收盘后真值验证流程

```text
T+1 收盘后
    ↓
CNSVdata 读取 T+1 收盘价
    ↓
生成 T 日对应的 t1_truth_vs_1400 标签
    ↓
CNSV 主程序读取预测记录与真值标签
    ↓
生成 validation 结果
    ↓
计算命中率、误差、校准度、区间覆盖率
    ↓
更新机器学习训练集
    ↓
必要时触发模型再训练或校准
```

---

## 6. CNSVdata 总体数据层设计

CNSVdata 需要新增一条独立数据线，不污染现有收盘后 processed 主线。

建议新增目录：

```text
data/intraday/snapshots/YYYYMMDD/1400/
data/intraday/replay/YYYYMMDD/1400/
data/labels/t1_truth/
data/ml_dataset/t1_intraday/
data/preview/intraday/
metadata/intraday/
data/quality/intraday/
```

其中：

1. snapshots：真实盘中运行产生的快照。
2. replay：历史重放生成的模拟 14:00 快照。
3. labels：T+1 真值标签。
4. ml_dataset：训练样本底座。
5. preview：人工查看 CSV。
6. metadata：快照 manifest、ready、lineage。
7. quality：盘中质量检查结果。

---

## 7. CNSV 主程序总体模块设计

CNSV 主程序应新增独立模块，不要打乱原 CNSV 收盘后主线。

建议新增：

```text
src/cnsv/intraday_line/
config/intraday_line.yml
data/predictions/intraday_line/
data/validation/intraday_line/
data/reports/intraday_line/
models/intraday_line/
reports/intraday_line/
```

核心模块：

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
```

---

## 8. 预测输出标准

CNSV 主程序必须至少输出以下字段：

```text
trade_date
asof_time
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
data_quality_status
model_version
feature_version
training_sample_count
risk_flags
manual_decision_reference
created_at
```

说明：

1. pred_up_prob：预测 T+1 收盘价高于 T 日 14:00 价格的概率。
2. pred_down_prob：预测 T+1 收盘价低于 T 日 14:00 价格的概率。
3. pred_return：预测 T+1 收盘相对 T 日 14:00 的涨跌幅。
4. pred_price_low / mid / high：T+1 收盘价格区间。
5. model_confidence：模型置信度，不等于上涨概率。
6. risk_flags：风险标签，例如数据延迟、波动率异常、冲高回落、量价背离。
7. manual_decision_reference：人工参考状态，不是交易指令。

---

## 9. 人工决策辅助输出边界

允许输出：

```text
观察
谨慎观察
风险偏高
禁止追高
只适合小仓试错
不适合作为强信号
```

谨慎输出：

```text
买入参考
减仓参考
继续观察
```

禁止输出：

```text
必须买入
必须卖出
满仓
梭哈
稳赚
明天一定涨停
自动下单
```

原因：

本项目定位是人工决策辅助系统，不是自动交易系统，也不是确定性预测系统。

---

## 10. 机器学习闭环要求

### 10.1 样本定义

每一个样本必须由两部分组成：

```text
X = T 日 14:00 以前的盘中特征
y = T+1 收盘价相对于 T 日 14:00 价格的真实收益
```

任何 T 日 14:00 之后的数据不得进入 X。

---

### 10.2 训练任务

至少包含两个任务：

1. 方向分类任务  
   预测 T+1 是否上涨。

2. 收益回归任务  
   预测 T+1 收盘相对 T 日 14:00 的涨跌幅。

建议增加第三个任务：

3. 分位数区间任务  
   预测 T+1 价格低位、中位、高位区间。

---

### 10.3 模型类型

第一阶段建议从稳健模型开始：

1. Logistic Regression / Ridge Classifier
2. Random Forest
3. Gradient Boosting
4. LightGBM 或 XGBoost，如果环境允许
5. Quantile Regression，用于价格区间
6. 简单 Ensemble，用于稳定输出

不要一开始就追求复杂深度学习。样本不足时，复杂模型更容易过拟合。

---

### 10.4 校准要求

概率输出必须做校准，不允许只看 raw probability。

至少支持：

1. Brier Score
2. Calibration Curve
3. 分桶命中率
4. Platt Scaling 或 Isotonic Regression

---

### 10.5 再训练要求

模型不能每次无规则乱训练。

建议规则：

1. 每日新增真值后，先追加样本。
2. 每周或每 N 个新样本触发一次再训练。
3. 样本数低于最低阈值时，只允许 baseline 模型。
4. 新模型必须通过 walk-forward 验证，才允许替换旧模型。
5. 新模型效果差于旧模型时，必须保留旧模型。
6. 每个模型必须有 model_version、train_window、feature_version、metrics_summary。

---

## 11. 验证指标

必须固定以下指标：

### 11.1 方向类指标

```text
direction_hit_rate
auc
precision_when_pred_up
recall_when_actual_up
brier_score
log_loss
calibration_bucket_accuracy
```

### 11.2 收益类指标

```text
mae
rmse
mean_error
median_error
spearman_ic
pearson_corr
```

### 11.3 区间类指标

```text
price_interval_hit_rate
lower_breach_rate
upper_breach_rate
interval_width_mean
```

### 11.4 实盘辅助类指标

```text
coverage_rate
high_confidence_hit_rate
low_confidence_filter_effect
drawdown_warning_hit_rate
```

---

## 12. 防未来函数要求

这是本项目最高级别硬约束。

任何 14:00 预测不得使用：

1. T 日 14:00 之后分钟线。
2. T 日收盘价。
3. T 日收盘后 moneyflow。
4. T+1 开盘价。
5. T+1 收盘价。
6. T+1 任意行情。
7. 用全样本训练后再回测历史。
8. 先知道真值再生成特征。
9. 使用文件修改时间暗含未来信息。
10. 使用未来 corporate action 信息影响历史预测。

如果发现未来函数，当前版本验收必须 FAIL。

---

## 13. 数据 ready 规则

CNSV 主程序读取 CNSVdata 盘中数据前，必须先读取：

```text
metadata/intraday/intraday_ready_1400.json
```

只有以下条件同时满足，才允许生成正式观察级预测：

```text
ready = true
status in ["PASS", "WARN"]
allowed_usage.can_run_intraday_forecast = true
allowed_usage.can_generate_formal_signal = false
```

说明：

1. PASS：允许生成正常观察级预测。
2. WARN：允许生成低置信观察级预测，报告必须明显提示风险。
3. FAIL：不得生成预测报告，只能输出阻断原因。
4. can_generate_formal_signal 必须始终为 false，表示不生成正式交易信号。

---

## 14. 版本路线

### V1.0 总需求冻结

完成三份文档：

1. CNSV 盘中线总需求.MD
2. CNSV 盘中线CNSVdata数据需求.MD
3. CNSV 盘中线CNSV主程序需求.MD

---

### V1.1 CNSVdata 盘中快照层

目标：

1. 14:00 快照生成。
2. 1min / 5min / 15min 盘中 bar。
3. 快照质量检查。
4. intraday_ready_1400.json。
5. CSV preview。

---

### V1.2 CNSVdata 真值标签层

目标：

1. T+1 收盘真值。
2. actual_return_vs_1400。
3. up/down/flat 标签。
4. truth_ready。
5. label manifest。

---

### V1.3 CNSVdata 历史重放与训练样本层

目标：

1. 历史 14:00 快照重放。
2. t1_intraday_trainset。
3. feature manifest。
4. label manifest。
5. 防未来函数检查。

---

### V1.4 CNSV 主程序预测接线层

目标：

1. 读取 CNSVdata 盘中快照。
2. 构建特征。
3. baseline 模型预测。
4. 输出预测报告。
5. 保存 prediction record。

---

### V1.5 CNSV 主程序验证闭环层

目标：

1. 读取 T+1 真值。
2. 验证预测是否命中。
3. 计算全部指标。
4. 生成 validation report。
5. 更新训练样本。

---

### V1.6 CNSV 主程序机器学习增强层

目标：

1. 多模型训练。
2. 概率校准。
3. 价格区间预测。
4. walk-forward 回测。
5. 模型注册与回滚。

---

### V2.0 人工尾盘决策辅助系统

目标：

1. 稳定日常运行。
2. 输出尾盘人工决策看板。
3. 有明确模型置信度。
4. 有历史命中率追踪。
5. 可作为用户实盘人工辅助工具。

---

## 15. 总体验收标准

### 15.1 数据验收

CNSVdata 必须满足：

1. 能生成 T 日 14:00 快照。
2. 能确认 09:30 - 11:30、13:00 - 14:00 覆盖情况。
3. 能识别缺分钟、重复分钟、价格异常、成交量异常。
4. 能生成 asof_price_1400。
5. 能生成 T+1 真值。
6. 能生成训练样本底座。
7. 所有输出有 manifest、quality、ready。
8. 不生成任何预测和交易信号。

---

### 15.2 模型验收

CNSV 主程序必须满足：

1. 只使用 14:00 以前数据。
2. 能输出涨跌概率。
3. 能输出预期涨跌幅。
4. 能输出价格区间。
5. 能保存预测记录。
6. T+1 后能验证预测。
7. 能计算固定指标。
8. 能进行 walk-forward 验证。
9. 能记录 model_version 和 feature_version。
10. 不自动交易。

---

### 15.3 报告验收

报告必须包含：

1. T 日和 T+1 日期。
2. T 日 14:00 价格。
3. T+1 预测涨跌概率。
4. T+1 预测涨跌幅。
5. T+1 预测价格区间。
6. 模型置信度。
7. 数据质量状态。
8. 主要风险解释。
9. 历史近 N 次命中情况。
10. 人工决策参考，不得输出确定性交易指令。

---

## 16. Codex 开发总原则

Codex 开发时必须遵守：

1. 不推翻现有 CNSVdata 主线。
2. 不污染 data/processed 收盘后主线。
3. 新增盘中线必须独立目录、独立脚本、独立 workflow、独立 ready 文件。
4. CNSVdata 不得出现预测字段。
5. CNSV 主程序不得绕过 CNSVdata ready 开关。
6. 所有字段必须有 schema。
7. 所有输出必须有 manifest。
8. 所有关键脚本必须有 pytest。
9. 所有时间必须明确是北京时间还是 UTC。
10. 所有 GitHub Actions cron 必须标注北京时间含义。
11. 所有预测必须可追溯到输入快照、模型版本和特征版本。
12. 宁可 FAIL，也不能伪装 PASS。

---

## 17. 项目最终定位

《CNSV 盘中线》不是简单加一个盘中脚本，而是一条完整的量化分支系统：

```text
盘中快照
    ↓
T+1 预测
    ↓
市场真值验证
    ↓
机器学习更新
    ↓
人工尾盘决策辅助
```

最终目标不是“每天给一个看起来漂亮的预测”，而是形成一个长期可验证、可进化、可风控的专业级盘中量化辅助系统。
