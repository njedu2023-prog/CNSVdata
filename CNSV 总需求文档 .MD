# CNSV 中国船舶专业量化波段系统总需求文档 V3.0

## 0. 文档定位

本文档是 `CNSV` 主程序仓库的 V3.0 专业可验证版总需求文档。

`CNSV` 是中国船舶 `600150.SH` 专用的专业量化研究、价格路径预测、人工波段操作、风险控制、回测验证和模型治理系统。

系统不是自动交易机器人。  
系统不连接券商交易接口。  
系统不自动下单。  
系统不直接替用户做买卖决策。

系统只负责：

```text
数据读取
数据校验
时点数据管理
价格路径预测
价格分布预测
交易机会评估
账户风险预算
人工执行计划
真实成交仿真
回测验证
影子运行
报告输出
模型治理
复盘审计
```

最终买卖由人工完成。

---

## 1. V3.0 核心升级原则

V3.0 与 V2.0 的核心区别：

```text
V2.0 = 功能蓝图
V3.0 = 可验证、可证伪、可审计的量化规范
```

系统必须遵守三条总原则：

```text
先验证，后信号
先预测完整路径，后生成买卖区间
先按账户风险定仓位，不按主观分数定仓位
```

在完整回测、样本外验证、成交仿真和风险预算未通过之前，系统不得输出正式买入、加仓、清仓等实盘指令。

---

## 2. 系统运行模式

系统必须区分四种模式：

```text
research_mode       研究模式
backtest_mode       回测模式
shadow_mode         影子运行模式
live_assist_mode    人工实盘辅助模式
```

### 2.1 research_mode

只用于研究和模型调试。  
不得输出实盘建议。

### 2.2 backtest_mode

用于历史回测和参数验证。  
不得输出实盘建议。

### 2.3 shadow_mode

系统每天正常生成报告，但明确标记：

```text
不可用于真钱交易
仅用于观察与验证
```

### 2.4 live_assist_mode

只有在验证门槛通过后才允许开启。  
即使开启，也只输出人工辅助计划，不自动交易。

默认配置：

```yaml
deployment:
  live_signal_enabled: false
  validation_gate_passed: false
  shadow_mode: true
  allow_auto_order: false
```

---

## 3. 上游数据仓库边界

上游数据由 `CNSVdata` 提供。

`CNSV` 默认不直接调用 Tushare。

`TUSHARE_TOKEN` 默认只配置在：

```text
CNSVdata
```

`CNSV` 只读取 `CNSVdata` 产出的标准化数据、数据快照和质量报告。

---

## 4. 严格 A 股交易日历

系统所有时间窗口必须基于 A 股交易日历。

定义：

```text
T = 最新完整 A 股交易日
T+1 = 下一个 A 股开市交易日
20D = 未来 20 个 A 股交易日
60D = 未来 60 个 A 股交易日
120D = 未来 120 个 A 股交易日
```

报告中必须输出：

```text
当前交易日
下一个交易日
未来20个交易日截止日
未来60个交易日截止日
未来120个交易日截止日
```

不得用自然日代替交易日。

---

## 5. 时点数据体系

系统必须支持时点数据。

每一类数据必须记录：

```text
observation_time
available_at
source
source_version
data_snapshot_id
data_snapshot_hash
```

含义：

```text
observation_time = 数据描述的实际发生时间
available_at = 该数据在当时市场上真正可获得的时间
```

训练和回测只能使用当时已经可获得的数据。

禁止使用未来才知道的信息。

---

## 6. 价格体系与复权规则

系统必须区分三类价格：

```text
raw_executable_price     原始可成交价格
adjusted_return_price    复权收益价格
research_price           研究用标准化价格
```

### 6.1 执行价格

买卖、止损、止盈、成交仿真必须使用原始可成交价格。

### 6.2 收益研究

收益研究可以使用复权收益，但必须保证时点正确。

### 6.3 公司行为

必须单独记录：

```text
分红
送转
配股
除权
停牌
复牌
换股
吸收合并
股本变化
```

不得用今天生成的完整前复权序列直接模拟过去交易。

---

## 7. 中国船舶结构断点处理

中国船舶吸收合并中国重工属于重大结构断点。

系统必须增加：

```yaml
entity_regime:
  - id: "legacy_cssc_before_merger"
    description: "合并前中国船舶"
  - id: "merger_transition"
    description: "吸收合并过渡期"
  - id: "combined_cssc_after_merger"
    description: "合并后中国船舶"
```

必须处理：

```text
合并前后股本变化
成交额可比性
换手率可比性
市值口径变化
财务报表口径变化
同行池变化
估值基准变化
```

中国重工在合并后不应继续作为独立同行标的使用。

系统必须在结构断点附近自动降低模型置信度，并触发重新校准。

---

## 8. 同类标的与生态池

同类标的池不用于直接推荐买卖。  
只用于生态强弱、相对强弱和板块共振判断。

合并后同类池第一版建议：

```text
中船防务
中国动力
中船科技
亚星锚链
江龙船艇
国瑞科技
军工ETF
中证军工
上证指数
沪深300
中证500
船舶制造相关指数
```

系统必须输出：

```text
中国船舶相对同类强弱
中国船舶相对军工板块强弱
中国船舶相对上证指数强弱
中国船舶是领涨、补涨、滞涨，还是被拖累
```

---

## 9. 账户状态模块

没有账户状态，就不能生成真正可执行的指令。

系统必须支持账户状态输入。

```json
{
  "account_state": {
    "nav": 0,
    "cash_available": 0,
    "position_qty": 0,
    "sellable_qty": 0,
    "today_bought_qty": 0,
    "average_cost": 0,
    "pending_orders": [],
    "strategy_capital_limit": 0
  }
}
```

系统建议不能只写“建议仓位 40%”。

必须进一步转换为：

```text
目标仓位
目标股数
当前仓位
需要买入多少股
需要卖出多少股
是否有可卖数量
是否现金足够
是否满足100股整数约束
```

---

## 10. 风险预算仓位模型

仓位不能只由信号分数决定。

仓位必须由账户风险预算决定。

核心公式：

```text
单笔允许账户风险 = 账户净值 × 单笔风险预算比例

每股压力风险 = 买入价 - 压力情景下预计止损成交价

建议买入股数 = 单笔允许账户风险 ÷ 每股压力风险
```

然后再叠加限制：

```text
最大策略仓位
最大个股仓位
可用现金
可卖数量
100股整数约束
流动性约束
跳空风险
模型置信度
数据置信度
事件风险
```

推荐配置：

```yaml
risk_budget:
  base_risk_per_trade_nav_pct: 0.005
  max_risk_per_trade_nav_pct: 0.010
  max_strategy_drawdown_pct: 0.10
  max_position_pct_of_total_nav: 0.40
  gap_risk_multiplier: 1.50
```

V3.0 不再默认使用 80% 最大仓位作为专业仓位依据。  
80% 可以作为绝对上限，但不能作为默认目标。

---

## 11. 预测标签定义

系统不得只输出看起来精确的价格数字。  
所有预测必须有明确标签定义。

### 11.1 终点收益

```text
terminal_return_h = ln(close[t+h] / close[t])
```

### 11.2 跳空收益

```text
gap_return_1d = ln(next_open / current_close)
```

### 11.3 最大有利波动

```text
MFE_h = max(high[t+1:t+h] / close[t] - 1)
```

### 11.4 最大不利波动

```text
MAE_h = min(low[t+1:t+h] / close[t] - 1)
```

### 11.5 最大回撤

```text
max_drawdown_h = 预测路径内从高点到低点的最大回撤
```

### 11.6 目标先于止损概率

```text
target_before_stop_prob = 目标价先于止损价被触及的概率
```

---

## 12. 价格路径预测，而不是孤立 OHLC 预测

系统最终必须生成完整未来价格路径。

路径示意：

```text
path_1
path_2
path_3
...
path_N
```

所有价格分布和风险指标必须从同一批路径计算。

包括：

```text
终点价格分布
期间最高价分布
期间最低价分布
触碰关键价格概率
目标先到概率
止损先到概率
MFE
MAE
最大回撤
首次到达时间
```

不得分别孤立预测开盘价、最高价、最低价、收盘价，导致价格关系互相矛盾。

---

## 13. 终点概率、触碰概率、先到概率必须分开

系统必须区分：

```text
终点概率
期间触碰概率
目标先到概率
首次到达时间
```

定义：

```text
终点概率 = 预测期末收盘价落在某区间的概率
期间触碰概率 = 预测期内任意时刻触碰某价格的概率
目标先到概率 = 目标价先于止损价触发的概率
首次到达时间 = 首次触碰目标价或止损价的预计交易日数
```

报告必须输出：

```json
{
  "path_probabilities": {
    "prob_touch_buy_zone": 0,
    "prob_touch_target": 0,
    "prob_touch_stop": 0,
    "prob_target_before_stop": 0,
    "prob_stop_before_target": 0,
    "median_days_to_target": null,
    "median_days_to_stop": null,
    "expected_mfe": 0,
    "expected_mae": 0,
    "expected_max_drawdown": 0
  }
}
```

---

## 14. 多周期预测边界

V3.0 必须降低第一版过度复杂度。

### 14.1 第一版重点

第一版重点做：

```text
20D 价格路径分布
20D 触碰概率
20D 目标先于止损概率
T+1 执行辅助
真实成交回测
账户风险预算
影子运行
```

### 14.2 T+1 定位

T+1 不作为整个波段系统核心。  
T+1 主要用于提高入场、减仓和止损执行质量。

### 14.3 60D 和 120D

60D 和 120D 不进入第一版正式信号。  
它们可以先作为研究型报告展示。

120D 更适合基本面、估值和行业周期情景模型，不应只靠技术指标。

---

## 15. 基准模型体系

第一版不建议使用深度学习和强化学习。

系统必须先建立透明基准模型：

```text
B0：不变价格或随机游走
B1：历史无条件收益分布
B2：按波动率和趋势状态分组的历史分布
B3：EWMA 或 GARCH 类波动模型
```

任何复杂模型必须在严格样本外验证中稳定优于基准模型，才允许进入候选模型。

---

## 16. 样本外验证

系统必须采用滚动样本外验证。

不得随机打乱时间序列。

对于 20D、60D、120D 重叠标签，必须使用：

```text
Purged walk-forward
Embargo
Block bootstrap
有效样本量报告
```

验证报告必须输出：

```text
样本外样本数
有效样本数
预测分位校准
区间覆盖率
Pinball Loss
Brier Score
基准模型对比
最大回撤
净收益
参数稳定性
```

---

## 17. 真实成交仿真

价格触碰不等于成交。

回测必须模拟：

```text
委托时间
限价委托
部分成交
未成交
撤单
滑点
跳空穿越
涨跌停
停牌
T+1 可卖限制
当日买入不可卖
交易成本
人工延迟
```

交易成本至少包括：

```text
佣金
印花税
过户费
滑点
冲击成本
```

系统必须支持：

```text
晚买5分钟
晚买15分钟
晚买30分钟
晚卖5分钟
晚卖15分钟
晚卖30分钟
```

如果策略必须在极短时间内执行才有效，则不适合人工系统。

---

## 18. 决策层与预测层分离

预测层只回答：

```text
未来可能怎么走
```

决策层回答：

```text
扣除成本后是否值得交易
```

执行层回答：

```text
具体买多少股
什么价格
什么时段有效
什么条件撤销
```

三层不得混在一起。

买入必须同时满足：

```text
预测净期望为正
目标先于止损概率合格
尾部风险受控
交易成本后仍有优势
账户风险预算允许
模型未漂移
没有重大事件禁入
数据置信度合格
```

---

## 19. 决策字段

JSON 必须增加：

```json
{
  "decision": {
    "expected_gross_return": 0,
    "expected_cost": 0,
    "expected_net_return": 0,
    "expected_shortfall_95": 0,
    "no_trade": true,
    "no_trade_reason": "",
    "target_position_pct": 0,
    "target_qty": 0,
    "delta_qty": 0,
    "side": "buy|sell|none",
    "limit_price": 0,
    "max_acceptable_price": 0,
    "valid_from": "",
    "valid_until": "",
    "cancel_conditions": []
  }
}
```

没有正净期望时，系统必须输出：

```text
不交易
```

不能因为上涨概率看起来较高就强行给买入。

---

## 20. 验证门槛

正式信号必须通过验证门槛。

```yaml
validation_gate:
  min_oos_sample_size: 80
  min_effective_sample_size: 30
  require_positive_net_expectancy: true
  require_better_than_buy_hold: true
  require_better_than_baseline_distribution: true
  max_allowed_drawdown_pct: 0.12
  require_probability_calibration: true
  require_execution_simulation: true
```

未通过时：

```text
只允许输出研究报告
不得输出正式买入、加仓、清仓建议
```

---

## 21. 模型治理：冠军—挑战者机制

第一版自学习只允许记录、诊断和提出建议。

禁止模型自动替换线上模型。

治理规则：

```text
当前线上模型 = champion
候选模型 = challenger
```

challenger 必须：

```text
离线运行
通过完整样本外验证
通过参数稳定性测试
通过真实成交仿真
由人工批准上线
支持一键回滚
```

模型自动调阈值不得直接影响正式信号。

---

## 22. 模型漂移监控

系统必须监控：

```text
预测误差扩大
分布校准变差
胜率连续下降
盈亏比下降
最大回撤扩大
信号过度频繁
信号长期不触发
阈值失效
结构断点出现
```

出现漂移时：

```text
降低信号等级
降低仓位建议
关闭正式信号
进入影子运行
触发重新校准
```

---

## 23. 数据清单 V3.0

### 23.1 第一版必须数据

```text
trade_calendar.parquet
cnsv_daily_raw.parquet
cnsv_1min_raw.parquet
cnsv_moneyflow.parquet
corporate_actions.parquet
structural_breaks.parquet
account_state.json
data_manifest.json
```

### 23.2 第二阶段数据

```text
valuation_pit.parquet
fundamentals_pit.parquet
corporate_announcements.parquet
peer_daily.parquet
index_daily.parquet
industry_daily.parquet
```

### 23.3 第三阶段数据

```text
orders_events.parquet
shipbuilding_cycle.parquet
newbuilding_price_index.parquet
steel_price.parquet
usd_cny.parquet
shipping_indices.parquet
macro_releases_pit.parquet
event_tags.parquet
```

---

## 24. 仓库目录结构 V3.0

```text
CNSV/
├── .github/
│   └── workflows/
│       ├── run_research.yml
│       ├── run_backtest.yml
│       ├── run_shadow_signal.yml
│       ├── run_model_validation.yml
│       └── publish_pages.yml
├── config/
│   ├── strategy.yml
│   ├── risk_budget.yml
│   ├── model.yml
│   ├── data_source.yml
│   ├── ecosystem.yml
│   ├── validation_gate.yml
│   └── report.yml
├── src/
│   └── cnsv/
│       ├── data/
│       │   ├── loader.py
│       │   ├── validator.py
│       │   ├── point_in_time.py
│       │   ├── corporate_actions.py
│       │   ├── structural_breaks.py
│       │   ├── data_manifest.py
│       │   └── trade_calendar.py
│       ├── portfolio/
│       │   ├── account_state.py
│       │   ├── holdings.py
│       │   └── pnl_attribution.py
│       ├── execution/
│       │   ├── a_share_rules.py
│       │   ├── fill_model.py
│       │   ├── transaction_cost.py
│       │   ├── limit_state.py
│       │   └── order_simulator.py
│       ├── features/
│       │   ├── trend_features.py
│       │   ├── minute_structure_features.py
│       │   ├── volatility_features.py
│       │   ├── moneyflow_features.py
│       │   ├── ecosystem_features.py
│       │   └── relative_strength_features.py
│       ├── models/
│       │   ├── baselines.py
│       │   ├── path_sampler.py
│       │   ├── first_passage.py
│       │   ├── quantile_calibration.py
│       │   ├── band_engine.py
│       │   ├── scenario_engine.py
│       │   ├── confidence_engine.py
│       │   ├── drift_monitor.py
│       │   └── self_learning.py
│       ├── decision/
│       │   ├── expected_value.py
│       │   ├── risk_budget_position.py
│       │   ├── no_trade_rules.py
│       │   └── manual_plan.py
│       ├── validation/
│       │   ├── purged_walk_forward.py
│       │   ├── embargo.py
│       │   ├── probability_calibration.py
│       │   ├── robustness_test.py
│       │   ├── multiple_testing.py
│       │   └── benchmark_comparison.py
│       ├── backtest/
│       │   ├── backtest_engine.py
│       │   ├── distribution_backtest.py
│       │   ├── execution_backtest.py
│       │   ├── metrics.py
│       │   └── execution_delay_test.py
│       ├── governance/
│       │   ├── model_registry.py
│       │   ├── promotion_gate.py
│       │   ├── rollback.py
│       │   └── immutable_signal_log.py
│       └── report/
│           ├── report_schema.py
│           ├── report_json.py
│           ├── report_md.py
│           ├── report_html_data.py
│           └── publish_report.py
├── reports/
├── docs/
├── models/
├── validation/
├── tests/
├── requirements.txt
└── README.md
```

---

## 25. JSON 报告结构 V3.0

```json
{
  "meta": {
    "version": "3.0",
    "ts_code": "600150.SH",
    "name": "中国船舶",
    "mode": "shadow_mode"
  },
  "provenance": {
    "signal_id": "",
    "model_version": "",
    "data_snapshot_id": "",
    "data_snapshot_hash": "",
    "generated_at": "",
    "data_cutoff_at": "",
    "valid_until": "",
    "entity_regime_id": "",
    "code_commit_sha": ""
  },
  "trade_calendar": {
    "trade_date": "",
    "next_trade_date": "",
    "horizon_20d_end": "",
    "horizon_60d_end": "",
    "horizon_120d_end": ""
  },
  "account_state": {
    "nav": 0,
    "cash_available": 0,
    "position_qty": 0,
    "sellable_qty": 0,
    "today_bought_qty": 0,
    "average_cost": 0,
    "pending_orders": []
  },
  "forecast_definition": {
    "price_type": "raw_executable_price",
    "return_type": "log_return",
    "horizon_unit": "trading_day",
    "terminal_or_path": "both"
  },
  "price_distribution": {
    "d20": {
      "terminal": {},
      "path": {}
    },
    "d60_research_only": {},
    "d120_research_only": {}
  },
  "path_risk": {
    "prob_touch_buy_zone": 0,
    "prob_touch_stop": 0,
    "prob_target_before_stop": 0,
    "prob_stop_before_target": 0,
    "expected_mfe": 0,
    "expected_mae": 0,
    "expected_shortfall_95": 0,
    "gap_beyond_stop_prob": 0
  },
  "decision": {
    "expected_gross_return": 0,
    "expected_cost": 0,
    "expected_net_return": 0,
    "no_trade": true,
    "no_trade_reason": "",
    "target_position_pct": 0,
    "target_qty": 0,
    "delta_qty": 0,
    "side": "buy|sell|none",
    "limit_price": 0,
    "valid_until": "",
    "cancel_conditions": []
  },
  "execution_plan": {
    "manual_action": "",
    "order_type": "",
    "valid_time_window": "",
    "cancel_conditions": []
  },
  "validation": {
    "validation_gate_passed": false,
    "oos_sample_size": 0,
    "effective_sample_size": 0,
    "p10_calibration": 0,
    "p50_calibration": 0,
    "p90_calibration": 0,
    "interval_80_coverage": 0,
    "pinball_loss": 0,
    "baseline_pinball_loss": 0,
    "net_backtest_return": 0,
    "max_drawdown": 0,
    "buy_hold_max_drawdown": 0
  },
  "model_drift": {
    "drift_detected": false,
    "drift_level": "",
    "reason": "",
    "action": ""
  },
  "forbidden_actions": [],
  "review": {}
}
```

---

## 26. 报告页面要求

Markdown 和 HTML 报告必须同时展示：

```text
运行模式
是否允许实盘使用
验证门槛是否通过
数据快照编号
模型版本
交易日历
账户状态
20D价格路径分布
触碰概率
目标先到/止损先到概率
净期望
交易成本
建议动作
不交易原因
真实成交仿真摘要
样本外验证摘要
模型漂移状态
禁止动作
人工复盘区
```

如果处于 `shadow_mode`，页面必须醒目标注：

```text
影子运行：本报告仅用于验证，不构成实盘操作依据
```

---

## 27. 第一版 MVP 重排

V3.0 第一版 MVP 必须缩小范围。

### 27.1 第一版必须完成

```text
日线原始价格数据
规范化1分钟数据
交易日历
公司行为表
合并结构断点表
账户状态输入
20D路径分布
20D触碰概率
20D目标先到/止损先到概率
基准模型
真实成交仿真
交易成本模型
样本外验证
买入持有基准对比
影子运行报告
JSON/MD/HTML三件套
```

### 27.2 第一版暂不完成

```text
T+1完整开高低收预测
60D正式交易信号
120D正式交易信号
新闻NLP
自动阈值修正
自动模型升级
A+强买入评级
高置信实盘信号
大量复杂网页功能
```

---

## 28. 项目阶段重排

```text
阶段0：数据契约、公司行为、结构断点、账户状态
阶段1：基准模型、价格路径、执行仿真、完整回测
阶段2：Purged walk-forward、概率校准、压力测试
阶段3：影子运行，只出报告，不用于真钱
阶段4：小仓位人工试运行
阶段5：持续验证通过后提高风险预算
阶段6：增加60D、120D和事件模型
阶段7：挑战者模型与人工批准升级
```

正式信号必须在阶段4之后才允许出现。

---

## 29. 风险控制硬规则

系统必须遵守：

```text
未通过验证门槛，不得输出正式买入信号
数据异常，不得输出强信号
模型漂移，不得输出强信号
账户现金不足，不得输出买入指令
无可卖数量，不得输出卖出指令
跌破硬止损，不得补仓
跳空穿越止损，要按压力成交价估算
触碰价格不等于成交
盈亏比合格不等于净期望合格
人工执行偏差不得算成模型错误
```

---

## 30. 最终结论

`CNSV` 的核心不是生成一堆漂亮价格预测。

它的核心是建立一个可以被验证、复盘和审计的专业系统：

```text
数据是否真实
交易日是否正确
价格路径是否有数学定义
预测是否经过样本外验证
成交是否真实可模拟
仓位是否来自账户风险预算
模型是否可回滚
人工执行是否可复盘
```

V3.0 的最终目标：

```text
不是让系统看起来专业
而是让系统在真钱交易前先经得起验证
```
