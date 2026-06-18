# CNSV 中国船舶实盘人工量化波段系统总需求文档 V3.2

## 0. 文档定位

本文档是 `CNSV` 主程序仓库的最终版总需求文档。

`CNSV` 是中国船舶 `600150.SH` 专用的实盘人工量化波段操作系统。

系统最终用途是服务真实股票账户中的人工买卖操作。

系统不是纯研究系统。  
系统不是纸面模拟系统。  
系统不是自动交易机器人。

系统不自动下单。  
系统不连接券商交易接口。  
系统不替代人工点击买入、卖出、撤单。

但系统必须为人工实盘操作提供可执行的量化决策依据。

系统每天必须回答以下实盘问题：

```text
今天能不能买？
如果能买，买多少？
什么价格买？
什么条件下不能买？
持仓时要不要加仓？
冲高到哪里减仓？
跌破哪里止损？
当前账户能不能执行？
如果判断错误，最大风险是多少？
人工执行时要注意什么？
```

`CNSV` 的核心定位：

```text
实盘人工买卖决策系统
实盘仓位管理系统
实盘风险预算系统
实盘价格路径预测系统
实盘执行计划系统
实盘复盘审计系统
```

---

## 1. 项目基本信息

### 1.1 仓库名称

```text
CNSV
```

### 1.2 上游数据仓库

```text
CNSVdata
```

`CNSVdata` 负责拉取、清洗、标准化、保存数据。  
`CNSV` 负责读取数据、计算模型、生成信号、输出报告。

### 1.3 标的对象

```text
股票代码：600150.SH
股票名称：中国船舶
市场：A 股 / 上交所
系统类型：单标的实盘人工量化波段系统
执行方式：人工手动买卖
```

### 1.4 Tushare TOKEN 原则

`TUSHARE_TOKEN` 默认只配置在：

```text
CNSVdata
```

`CNSV` 默认不配置 `TUSHARE_TOKEN`。

原因：

```text
CNSVdata = 数据层
CNSV = 模型层 / 决策层 / 报告层
```

`CNSV` 不应重复拉取 Tushare 数据，避免上下游数据不一致。

---

## 2. 系统价值定位

`CNSV` 的价值不是生成漂亮报告，而是辅助人工完成真实交易。

系统必须服务以下真实场景：

```text
盘前制定今日操作计划
盘中判断低吸、持有、减仓、止损
盘后复盘系统建议和人工执行偏差
持仓期间动态调整仓位
不同价格路径下制定应对动作
```

系统不允许只输出：

```text
上涨概率
趋势较强
支撑附近
注意风险
```

系统必须输出：

```text
目标仓位
目标股数
买入区间
卖出区间
止损价格
撤单条件
禁止动作
有效时间
账户约束
风险预算
```

---

## 3. 核心原则

系统必须遵守以下原则：

```text
实盘用途明确
人工手动执行
不自动下单
先验证后放大信号
先预测完整路径
再生成买卖计划
先按账户风险定仓位
不按主观分数定仓位
```

### 3.1 实盘用途明确

`CNSV` 从第一版开始就面向实盘人工辅助。

验证门槛不是否定实盘用途。  
验证门槛用于控制：

```text
信号等级
仓位上限
执行权限
风险预算
```

### 3.2 人工执行

人工执行的含义是：

```text
系统负责算
系统负责给计划
系统负责给风险边界
系统负责给撤销条件
人工负责最后点击交易软件
人工负责确认是否执行
```

### 3.3 信号分级

系统不得把所有信号一刀切。

必须分级：

```text
L0 数据异常
L1 观察信号
L2 试运行信号
L3 正式辅助信号
L4 高置信信号
```

### 3.4 触碰不等于成交

价格碰到某个价位，不代表订单一定成交。

系统必须模拟：

```text
限价未成交
部分成交
跳空穿越
涨跌停
停牌
T+1 可卖限制
人工延迟
交易成本
滑点
```

---

## 4. 系统运行模式

系统必须支持四种模式：

```text
research_mode        实盘模型研发模式
backtest_mode        实盘回测验证模式
trial_assist_mode    实盘试运行辅助模式
live_assist_mode     实盘正式辅助模式
```

### 4.1 research_mode：实盘模型研发模式

该模式用于：

```text
模型研发
特征研究
参数调试
误差诊断
```

该模式围绕真实实盘需求研发。

允许输出：

```text
特征表现
历史统计
模型误差
价格分布草案
风险观察
模型改进建议
```

不允许输出：

```text
正式买入指令
正式加仓指令
正式清仓指令
正式仓位指令
```

---

### 4.2 backtest_mode：实盘回测验证模式

该模式用于判断系统是否具备真实实盘使用资格。

回测必须模拟真实 A 股约束：

```text
交易日历
涨跌停
停牌
T+1 可卖限制
当日买入不可卖
滑点
交易成本
跳空穿越
限价未成交
部分成交
人工延迟
```

回测目标不是做出好看的收益曲线，而是验证：

```text
真实交易约束下是否有正期望
是否优于买入持有
是否优于简单基准模型
是否能控制最大回撤
是否适合人工执行
```

---

### 4.3 trial_assist_mode：实盘试运行辅助模式

该模式用于真实市场中的低风险试运行。

允许输出：

```text
观察级信号
试运行级买入计划
低仓位辅助计划
风险提示
撤销条件
人工复盘记录
```

限制：

```text
不得输出高置信强买入
不得建议重仓
不得跳过验证门槛
不得忽略账户风险预算
```

---

### 4.4 live_assist_mode：实盘正式辅助模式

该模式是系统最终目标。

通过验证门槛后，系统进入正式实盘辅助模式。

可以输出：

```text
正式买入辅助信号
正式减仓辅助信号
正式清仓辅助信号
目标仓位
目标股数
买入价格区间
卖出价格区间
止损价格
撤单条件
禁止动作
```

系统仍然不自动下单。  
最终交易由人工手动完成。

---

## 5. 默认部署配置

第一版系统默认目标就是实盘人工辅助，但必须受验证门槛控制。

```yaml
deployment:
  target_usage: "live_manual_trading_assist"
  auto_order_enabled: false
  broker_api_enabled: false
  human_execution_required: true

  default_mode: "trial_assist_mode"

  live_signal_enabled: true
  validation_gate_required: true
  validation_gate_passed: false

  allow_observation_signal: true
  allow_low_risk_trial_signal: true
  allow_formal_signal: false
  allow_high_confidence_signal: false
```

字段含义：

```text
target_usage = 系统最终用途是实盘人工辅助
auto_order_enabled = 永不自动下单
broker_api_enabled = 不接券商接口
human_execution_required = 必须人工确认
default_mode = 第一版默认实盘试运行辅助
live_signal_enabled = 允许生成实盘辅助信号
validation_gate_required = 正式信号必须经过验证门槛
validation_gate_passed = 当前是否已经通过验证
allow_observation_signal = 允许观察级信号
allow_low_risk_trial_signal = 允许低风险试运行信号
allow_formal_signal = 未通过验证前禁止正式信号
allow_high_confidence_signal = 未通过验证前禁止高置信强信号
```

---

## 6. 信号等级

### 6.1 L0 数据异常

触发条件：

```text
数据缺失
交易日错误
结构断点未处理
账户状态缺失
核心字段异常
```

动作：

```text
禁止买入
禁止加仓
只允许风险提示
```

---

### 6.2 L1 观察信号

模型有方向判断，但验证不足。

动作：

```text
只观察
可记录
不建议实盘执行
```

---

### 6.3 L2 试运行信号

系统允许小仓位实盘试运行。

动作：

```text
允许低仓位
必须设置硬止损
必须记录人工执行
不得重仓
```

---

### 6.4 L3 正式辅助信号

系统通过验证门槛后，允许正式辅助人工交易。

动作：

```text
按账户风险预算执行
输出目标仓位
输出目标股数
输出买卖区间
输出撤销条件
```

---

### 6.5 L4 高置信信号

必须经过长期样本外验证和实盘复盘后才允许。

动作：

```text
可以提高仓位上限
仍不得超过风险预算
仍需人工确认
```

---

## 7. 严格 A 股交易日历

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

## 8. 时点数据体系

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

## 9. 价格体系与复权规则

系统必须区分三类价格：

```text
raw_executable_price
adjusted_return_price
research_price
```

### 9.1 raw_executable_price

用于：

```text
买卖
止损
止盈
成交仿真
限价委托
账户复盘
```

### 9.2 adjusted_return_price

用于：

```text
收益研究
历史收益计算
因子研究
```

### 9.3 research_price

用于：

```text
模型训练
归一化处理
跨周期比较
```

### 9.4 公司行为

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

## 10. 中国船舶结构断点处理

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

结构断点附近必须：

```text
降低模型置信度
触发重新校准
标注数据不可比风险
禁止高置信强信号
```

---

## 11. 同类标的与生态池

同类标的池不用于直接推荐买卖。

只用于：

```text
生态强弱
相对强弱
板块共振
风险归因
```

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

## 12. 账户状态模块

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

系统不能只写：

```text
建议仓位 40%
```

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

## 13. 风险预算仓位模型

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

80% 可以作为绝对上限。  
但 80% 不应作为默认目标仓位。

---

## 14. 预测标签定义

所有预测必须有明确数学定义。

### 14.1 终点收益

```text
terminal_return_h = ln(close[t+h] / close[t])
```

### 14.2 跳空收益

```text
gap_return_1d = ln(next_open / current_close)
```

### 14.3 最大有利波动

```text
MFE_h = max(high[t+1:t+h] / close[t] - 1)
```

### 14.4 最大不利波动

```text
MAE_h = min(low[t+1:t+h] / close[t] - 1)
```

### 14.5 最大回撤

```text
max_drawdown_h = 预测路径内从高点到低点的最大回撤
```

### 14.6 目标先于止损概率

```text
target_before_stop_prob = 目标价先于止损价被触及的概率
```

---

## 15. 价格路径预测

系统不得孤立预测开盘价、最高价、最低价、收盘价。

系统必须生成完整未来价格路径。

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

这样可以避免：

```text
预测最高价低于开盘价
预测最低价高于收盘价
开高低收互相矛盾
```

---

## 16. 终点概率、触碰概率、先到概率

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

JSON 必须包含：

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

## 17. 多周期预测边界

第一版必须控制复杂度。

### 17.1 第一版重点

第一版重点做：

```text
20D 价格路径分布
20D 触碰概率
20D 目标先于止损概率
T+1 执行辅助
真实成交回测
账户风险预算
实盘试运行辅助
```

### 17.2 T+1 定位

T+1 不作为整个波段系统核心。

T+1 用于提高：

```text
入场执行质量
减仓执行质量
止损执行质量
盘中人工判断质量
```

### 17.3 60D 和 120D

60D 和 120D 不进入第一版正式信号。

它们可以先作为研究型分布报告展示。

120D 更适合：

```text
基本面情景
估值情景
行业周期
订单周期
宏观流动性
```

不应只靠技术指标。

---

## 18. 基准模型体系

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

## 19. 样本外验证

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

## 20. 真实成交仿真

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

系统必须支持人工延迟测试：

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

## 21. 预测层、决策层、执行层分离

### 21.1 预测层

回答：

```text
未来可能怎么走？
```

输出：

```text
价格路径
分布区间
触碰概率
先到概率
最大不利波动
最大有利波动
```

### 21.2 决策层

回答：

```text
扣除成本后是否值得交易？
```

输出：

```text
预期毛收益
交易成本
预期净收益
尾部风险
是否交易
不交易原因
```

### 21.3 执行层

回答：

```text
具体怎么人工操作？
```

输出：

```text
买多少股
卖多少股
什么价格
什么时段有效
什么条件撤销
什么动作禁止
```

---

## 22. 买入成立条件

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
账户现金足够
价格未高开过度
```

没有正净期望时，系统必须输出：

```text
不交易
```

不能因为上涨概率看起来较高就强行给买入。

---

## 23. 决策字段

JSON 必须包含：

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

---

## 24. 验证门槛

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
允许观察级信号
允许低风险试运行信号
禁止高置信强信号
禁止重仓建议
```

---

## 25. 模型治理：冠军—挑战者机制

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

## 26. 模型漂移监控

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
关闭高置信信号
进入重新校准
触发人工复核
```

---

## 27. 数据清单

### 27.1 第一版必须数据

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

### 27.2 第二阶段数据

```text
valuation_pit.parquet
fundamentals_pit.parquet
corporate_announcements.parquet
peer_daily.parquet
index_daily.parquet
industry_daily.parquet
```

### 27.3 第三阶段数据

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

## 28. 仓库目录结构

```text
CNSV/
├── .github/
│   └── workflows/
│       ├── run_research.yml
│       ├── run_backtest.yml
│       ├── run_trial_signal.yml
│       ├── run_live_assist.yml
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

## 29. JSON 报告结构

```json
{
  "meta": {
    "version": "3.2",
    "ts_code": "600150.SH",
    "name": "中国船舶",
    "mode": "trial_assist_mode"
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
    "signal_level": "L0|L1|L2|L3|L4",
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
    "cancel_conditions": [],
    "forbidden_actions": []
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
  "review": {
    "system_action": "",
    "actual_action": "",
    "execution_match": null,
    "deviation_reason": "",
    "execution_score": null
  }
}
```

---

## 30. 报告页面要求

Markdown 和 HTML 报告必须同时展示：

```text
运行模式
信号等级
验证门槛状态
数据快照编号
模型版本
交易日历
账户状态
20D价格路径分布
触碰概率
目标先到概率
止损先到概率
预期净收益
预期交易成本
建议动作
不交易原因
真实成交仿真摘要
样本外验证摘要
模型漂移状态
禁止动作
人工复盘区
```

HTML 页面必须从：

```text
docs/data/latest_signal.json
```

读取数据。

不允许 HTML 写死字段。

Markdown 报告路径：

```text
reports/latest_signal.md
reports/archive/YYYY-MM-DD_signal.md
```

HTML 页面路径：

```text
docs/index.html
docs/decision.html
docs/distribution.html
docs/backtest.html
```

---

## 31. 第一版 MVP

第一版必须完成：

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
试运行辅助报告
JSON/MD/HTML三件套
```

第一版暂不完成：

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

## 32. 项目阶段

```text
阶段0：数据契约、公司行为、结构断点、账户状态
阶段1：基准模型、价格路径、执行仿真、完整回测
阶段2：Purged walk-forward、概率校准、压力测试
阶段3：实盘试运行辅助，低仓位受控
阶段4：正式实盘人工辅助
阶段5：持续验证后提高风险预算
阶段6：增加60D、120D和事件模型
阶段7：挑战者模型与人工批准升级
```

---

## 33. 风险控制硬规则

系统必须遵守：

```text
未通过验证门槛，不得输出高置信强信号
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

## 34. 禁用表达

全文不得使用以下表达：

```text
只用于研究
不得用于真钱交易
不构成实盘操作依据
不可用于实盘
系统不直接替用户做买卖决策
正式信号必须很晚才能出现
```

统一改成：

```text
用于实盘人工辅助
不自动下单
人工手动执行
受验证门槛控制
未通过验证时只允许观察级或低风险试运行级信号
正式信号必须通过验证门槛
系统为人工买卖提供量化决策依据
```

---

## 35. 最终结论

`CNSV` 的核心不是生成一堆漂亮价格预测。

它的核心是建立一个可以服务真实交易、可以验证、可以复盘、可以审计的专业实盘人工量化系统。

系统必须回答：

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

V3.2 的最终目标：

```text
不是让系统看起来专业
而是让系统真正服务实盘人工操作
```
