# CNSVdata 中国船舶实盘量化数据底座开发文档 V1.0

## 0. 文档定位

本文档是 `CNSVdata` 上游数据仓库的详细开发文档。

`CNSVdata` 是 `CNSV` 中国船舶实盘人工量化波段系统的数据底座仓库。

`CNSVdata` 不负责生成买卖信号。  
`CNSVdata` 不负责输出交易建议。  
`CNSVdata` 不负责模型预测。  
`CNSVdata` 只负责数据采集、数据标准化、数据质量检查、数据快照、数据血缘、交易日历、公司行为、结构断点和下游数据契约。

`CNSVdata` 的核心目标是：

```text
为 CNSV 主系统提供可复现、可审计、可回放、可校验的高质量数据底座。
```

如果 `CNSVdata` 不稳定，`CNSV` 的价格路径预测、触碰概率、风险预算、仓位建议和实盘人工操作计划都不可靠。

---

## 1. 仓库基本信息

### 1.1 仓库名称

```text
CNSVdata
```

### 1.2 仓库定位

```text
中国船舶 600150.SH 实盘人工量化系统上游数据仓库
```

### 1.3 服务对象

```text
CNSV 主程序仓库
```

### 1.4 核心标的

```text
ts_code: 600150.SH
name: 中国船舶
market: A 股 / 上交所
```

---

## 2. 总体架构原则

### 2.1 数据仓库只做数据

`CNSVdata` 只做：

```text
数据拉取
数据清洗
数据标准化
数据校验
数据快照
数据归档
交易日历
公司行为
结构断点
数据质量报告
下游读取契约
```

不做：

```text
买卖信号
仓位建议
价格预测
路径模拟
交易决策
HTML 报告
```

---

### 2.2 Tushare TOKEN 只放在 CNSVdata

`TUSHARE_TOKEN` 只配置在 `CNSVdata` 仓库的 GitHub Actions Secrets 中。

Secret 名称固定为：

```text
TUSHARE_TOKEN
```

代码中只能通过环境变量读取：

```python
import os

token = os.getenv("TUSHARE_TOKEN")
```

严禁把 TOKEN 写入：

```text
代码文件
配置文件
README
日志
报告
JSON
CSV
Parquet 元数据
```

---

### 2.3 1分钟数据作为分钟级唯一真源

第一版必须以 1 分钟数据作为分钟级唯一真源。

```text
1min = 外部原始数据源
5min / 15min / 30min / 60min = 由 1min 聚合生成
```

禁止长期同时从外部拉取多周期分钟数据作为平行真源。  
否则容易出现不同周期之间成交量、最高价、最低价、时间戳不一致。

---

### 2.4 原始数据与加工数据分离

必须分为：

```text
raw       原始层
processed 标准化层
quality   质量报告层
metadata  元数据层
```

原始层尽量少改动。  
加工层用于下游模型读取。  
质量层用于判断数据是否可用。  
元数据层用于审计和回放。

---

## 3. 推荐仓库目录结构

```text
CNSVdata/
├── .github/
│   └── workflows/
│       ├── fetch_daily.yml
│       ├── fetch_minute.yml
│       ├── build_processed.yml
│       └── data_quality_check.yml
├── config/
│   ├── target.yml
│   ├── tushare.yml
│   ├── calendar.yml
│   ├── schema.yml
│   └── data_contract.yml
├── scripts/
│   ├── fetch_trade_calendar.py
│   ├── fetch_cnsv_daily.py
│   ├── fetch_cnsv_1min.py
│   ├── fetch_moneyflow.py
│   ├── build_minute_bars.py
│   ├── build_corporate_actions.py
│   ├── build_structural_breaks.py
│   ├── build_processed_daily.py
│   ├── build_data_manifest.py
│   └── quality_check.py
├── data/
│   ├── raw/
│   │   ├── cnsv_daily_raw.parquet
│   │   ├── cnsv_1min_raw.parquet
│   │   ├── cnsv_moneyflow_raw.parquet
│   │   └── trade_calendar_raw.parquet
│   ├── processed/
│   │   ├── cnsv_daily.parquet
│   │   ├── cnsv_1min.parquet
│   │   ├── cnsv_5min.parquet
│   │   ├── cnsv_15min.parquet
│   │   ├── cnsv_30min.parquet
│   │   ├── cnsv_60min.parquet
│   │   ├── cnsv_moneyflow.parquet
│   │   ├── trade_calendar.parquet
│   │   ├── corporate_actions.parquet
│   │   └── structural_breaks.parquet
│   └── quality/
│       ├── data_quality_latest.json
│       ├── missing_minutes_report.json
│       ├── schema_check_latest.json
│       ├── minute_aggregation_check.json
│       └── latest_run_summary.json
├── metadata/
│   ├── latest_trade_date.json
│   ├── next_trade_date.json
│   ├── data_manifest.json
│   ├── data_snapshot.json
│   ├── fetch_status.json
│   ├── schema_version.json
│   └── downstream_contract.json
├── tests/
│   ├── test_trade_calendar.py
│   ├── test_minute_coverage.py
│   ├── test_no_duplicate_bars.py
│   ├── test_ohlcv_schema.py
│   ├── test_minute_aggregation.py
│   ├── test_corporate_actions.py
│   ├── test_structural_breaks.py
│   └── test_data_manifest.py
├── requirements.txt
└── README.md
```

---

## 4. 配置文件设计

## 4.1 `config/target.yml`

```yaml
target:
  ts_code: "600150.SH"
  name: "中国船舶"
  market: "A_SHARE"
  exchange: "SSE"
```

作用：

```text
统一标的代码
避免脚本里写死股票代码
方便后续扩展同类标的数据
```

---

## 4.2 `config/tushare.yml`

```yaml
tushare:
  token_env: "TUSHARE_TOKEN"
  retry_times: 3
  retry_sleep_seconds: 5
  minute_freq: "1min"
  minute_batch_limit: 8000
```

要求：

```text
只记录环境变量名
不得记录真实 TOKEN
```

---

## 4.3 `config/calendar.yml`

```yaml
calendar:
  exchange: "SSE"
  market: "A"
  trading_day_only: true
  timezone: "Asia/Shanghai"
```

---

## 4.4 `config/schema.yml`

定义所有输出文件的字段标准。

第一版至少定义：

```text
daily_schema
minute_schema
moneyflow_schema
trade_calendar_schema
corporate_actions_schema
structural_breaks_schema
```

---

## 4.5 `config/data_contract.yml`

这是给 `CNSV` 主仓库读取的契约。

必须明确：

```text
哪些文件必须存在
字段名是什么
字段类型是什么
时间字段格式是什么
缺失值如何处理
版本号是什么
```

---

## 5. 数据文件设计

## 5.1 交易日历

### 输出文件

```text
data/processed/trade_calendar.parquet
metadata/latest_trade_date.json
metadata/next_trade_date.json
```

### 字段要求

```text
cal_date
is_open
pretrade_date
exchange
```

### latest_trade_date.json

```json
{
  "latest_trade_date": "YYYY-MM-DD",
  "source": "tushare",
  "generated_at": "YYYY-MM-DD HH:mm:ss",
  "timezone": "Asia/Shanghai"
}
```

### next_trade_date.json

```json
{
  "current_trade_date": "YYYY-MM-DD",
  "next_trade_date": "YYYY-MM-DD",
  "source": "tushare",
  "generated_at": "YYYY-MM-DD HH:mm:ss",
  "timezone": "Asia/Shanghai"
}
```

### 校验要求

必须保证：

```text
周末不是交易日
节假日不是交易日
T+1 是下一个开市日
20D / 60D / 120D 只能按交易日计算
```

---

## 5.2 日线原始数据

### 原始文件

```text
data/raw/cnsv_daily_raw.parquet
```

### 标准化文件

```text
data/processed/cnsv_daily.parquet
```

### 字段要求

```text
ts_code
trade_date
open
high
low
close
pre_close
change
pct_chg
vol
amount
source
fetched_at
```

### 价格要求

日线原始价格必须是可成交原始价格。

不得在执行层使用未来生成的完整前复权价格。

---

## 5.3 1分钟原始数据

### 原始文件

```text
data/raw/cnsv_1min_raw.parquet
```

### 标准化文件

```text
data/processed/cnsv_1min.parquet
```

### 字段要求

```text
ts_code
trade_time
trade_date
time
open
high
low
close
vol
amount
source
fetched_at
```

### 时间要求

`trade_time` 必须是完整时间戳。

建议格式：

```text
YYYY-MM-DD HH:mm:ss
```

### A 股交易时段

正常交易时段：

```text
09:30 - 11:30
13:00 - 15:00
```

质量检查必须识别：

```text
上午缺失
下午缺失
中午非交易时间错误数据
重复分钟
异常分钟
```

---

## 5.4 5/15/30/60分钟数据

这些文件必须从 1 分钟数据聚合生成。

```text
data/processed/cnsv_5min.parquet
data/processed/cnsv_15min.parquet
data/processed/cnsv_30min.parquet
data/processed/cnsv_60min.parquet
```

### 聚合规则

```text
open = 周期内第一根1分钟 open
high = 周期内最高 high
low = 周期内最低 low
close = 周期内最后一根1分钟 close
vol = 周期内 vol 合计
amount = 周期内 amount 合计
```

必须生成聚合校验报告：

```text
data/quality/minute_aggregation_check.json
```

### 校验要求

必须检查：

```text
5min 成交量合计是否等于对应 1min 成交量
15min 最高价是否等于对应区间内最高价
30min 最低价是否等于对应区间内最低价
60min 收盘价是否等于对应区间最后1min收盘价
```

---

## 5.5 资金流数据

### 原始文件

```text
data/raw/cnsv_moneyflow_raw.parquet
```

### 标准化文件

```text
data/processed/cnsv_moneyflow.parquet
```

### 字段要求

```text
ts_code
trade_date
buy_sm_amount
sell_sm_amount
buy_md_amount
sell_md_amount
buy_lg_amount
sell_lg_amount
buy_elg_amount
sell_elg_amount
net_mf_amount
source
fetched_at
```

### 专业提醒

资金流数据不是交易所披露的真实“主力身份”。  
它通常是数据商按成交单大小推断出来的结果。

因此必须记录：

```text
source
source_version
field_definition
fetched_at
```

下游使用时必须允许对资金流降权。

---

## 5.6 公司行为表

### 输出文件

```text
data/processed/corporate_actions.parquet
```

### 需要记录

```text
dividend
bonus_share
rights_issue
ex_right
suspension
resumption
share_change
merger
share_swap
delisting_related
other
```

### 字段要求

```text
ts_code
event_date
available_at
event_type
event_name
description
raw_source
impact_level
created_at
```

### 作用

公司行为表用于：

```text
防止复权污染
处理股本变化
处理换股
处理吸收合并
解释历史价格断点
辅助模型降级
```

---

## 5.7 结构断点表

### 输出文件

```text
data/processed/structural_breaks.parquet
```

### 中国船舶必须记录的结构状态

```yaml
entity_regime:
  - id: "legacy_cssc_before_merger"
    description: "合并前中国船舶"

  - id: "merger_transition"
    description: "吸收合并过渡期"

  - id: "combined_cssc_after_merger"
    description: "合并后中国船舶"
```

### 字段要求

```text
regime_id
start_date
end_date
description
reason
impact_fields
model_action
created_at
```

### impact_fields 示例

```text
share_capital
market_cap
turnover_rate
amount
valuation
financial_statement
peer_pool
```

### model_action 示例

```text
reduce_confidence
reset_peer_pool
recalibrate_model
disable_high_confidence_signal
```

---

## 6. 数据快照与数据血缘

`CNSVdata` 必须生成数据快照。

### 输出文件

```text
metadata/data_snapshot.json
metadata/data_manifest.json
```

## 6.1 data_snapshot.json

```json
{
  "data_snapshot_id": "",
  "data_snapshot_hash": "",
  "generated_at": "",
  "latest_trade_date": "",
  "files": []
}
```

## 6.2 data_manifest.json

```json
{
  "snapshot_id": "",
  "generated_at": "",
  "latest_trade_date": "",
  "source": "tushare",
  "files": [
    {
      "path": "data/processed/cnsv_daily.parquet",
      "rows": 0,
      "columns": [],
      "sha256": "",
      "updated_at": ""
    }
  ]
}
```

### 用途

```text
CNSV 报告可追溯
历史回测可复现
数据异常可定位
模型输出可审计
```

---

## 7. 数据质量检查

质量检查脚本：

```text
scripts/quality_check.py
```

输出：

```text
data/quality/data_quality_latest.json
```

## 7.1 必查项目

```text
交易日历是否存在
最新交易日是否正确
日线数据是否存在
1分钟数据是否存在
1分钟数据是否有断档
是否有重复时间戳
OHLC 是否合理
成交量是否异常
成交额是否异常
聚合周期是否一致
资金流数据是否缺失
公司行为表是否存在
结构断点表是否存在
data_manifest 是否生成
```

## 7.2 OHLC 检查

每根 K 线必须满足：

```text
high >= open
high >= close
low <= open
low <= close
high >= low
```

## 7.3 分钟覆盖率检查

必须输出：

```text
expected_minutes
actual_minutes
missing_minutes
duplicate_minutes
coverage_ratio
```

报告文件：

```text
data/quality/missing_minutes_report.json
```

## 7.4 质量等级

```text
PASS
WARN
FAIL
```

含义：

```text
PASS = 数据可用于 CNSV 主系统
WARN = 可用于观察，但下游应降级置信度
FAIL = 不得用于生成正式信号
```

---

## 8. 下游数据契约

`CNSVdata` 必须向 `CNSV` 提供稳定契约。

### 8.1 CNSV 必须读取的文件

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

### 8.2 CNSV 判断逻辑

如果 `data_quality_latest.json` 为：

```text
PASS
```

CNSV 可正常运行。

如果为：

```text
WARN
```

CNSV 必须降低数据置信度。

如果为：

```text
FAIL
```

CNSV 不得输出正式买入、加仓、清仓信号。

---

## 9. GitHub Actions 设计

## 9.1 `fetch_daily.yml`

职责：

```text
拉取交易日历
拉取日线数据
拉取资金流数据
更新 latest_trade_date
```

建议运行时间：

```text
北京时间 16:10 以后
```

---

## 9.2 `fetch_minute.yml`

职责：

```text
拉取 1分钟数据
增量更新 raw 数据
标准化 1分钟数据
```

建议运行时间：

```text
北京时间 16:20 以后
```

---

## 9.3 `build_processed.yml`

职责：

```text
从 raw 生成 processed
从 1min 聚合 5/15/30/60min
生成公司行为表
生成结构断点表
生成 data_manifest
```

建议运行时间：

```text
北京时间 16:30 以后
```

---

## 9.4 `data_quality_check.yml`

职责：

```text
运行全部数据质量检查
输出质量报告
提交 data/quality
提交 metadata
```

建议运行时间：

```text
北京时间 16:40 以后
```

---

## 10. 脚本职责设计

## 10.1 `scripts/fetch_trade_calendar.py`

职责：

```text
拉取 A 股交易日历
生成 trade_calendar.parquet
生成 latest_trade_date.json
生成 next_trade_date.json
```

必须支持：

```text
判断最新完整交易日
判断下一个交易日
计算未来20D/60D/120D截止日
```

---

## 10.2 `scripts/fetch_cnsv_daily.py`

职责：

```text
拉取中国船舶日线行情
保存 raw
生成 processed
```

不得使用未来复权价格模拟交易。

---

## 10.3 `scripts/fetch_cnsv_1min.py`

职责：

```text
拉取中国船舶1分钟历史数据
增量更新
去重
按 trade_time 排序
保存 raw 和 processed
```

必须处理：

```text
接口限制
分页拉取
重复数据
缺失数据
异常返回
```

---

## 10.4 `scripts/fetch_moneyflow.py`

职责：

```text
拉取资金流数据
标准化字段
记录 source 和 fetched_at
```

---

## 10.5 `scripts/build_minute_bars.py`

职责：

```text
从 1min 聚合 5min
从 1min 聚合 15min
从 1min 聚合 30min
从 1min 聚合 60min
生成聚合校验报告
```

---

## 10.6 `scripts/build_corporate_actions.py`

职责：

```text
生成公司行为表
记录分红、除权、停牌、复牌、换股、合并
```

第一版可以先人工维护部分重大事件。  
后续再自动化抓取。

---

## 10.7 `scripts/build_structural_breaks.py`

职责：

```text
生成结构断点表
标记中国船舶吸收合并中国重工
标记模型降级区间
标记同行池重置区间
```

---

## 10.8 `scripts/build_data_manifest.py`

职责：

```text
扫描 processed 文件
计算行数
计算字段
计算 sha256
生成 data_manifest.json
生成 data_snapshot.json
```

---

## 10.9 `scripts/quality_check.py`

职责：

```text
运行所有质量检查
输出 PASS/WARN/FAIL
生成详细异常报告
```

---

## 11. 测试要求

必须有测试，不允许裸跑。

### 11.1 `tests/test_trade_calendar.py`

检查：

```text
交易日历文件存在
latest_trade_date 是交易日
next_trade_date 是未来开市日
20D/60D/120D 不使用自然日
```

---

### 11.2 `tests/test_minute_coverage.py`

检查：

```text
1分钟数据覆盖率
缺失分钟
重复分钟
非交易时间数据
```

---

### 11.3 `tests/test_no_duplicate_bars.py`

检查：

```text
daily 无重复 trade_date
1min 无重复 trade_time
聚合周期无重复时间戳
```

---

### 11.4 `tests/test_ohlcv_schema.py`

检查：

```text
字段是否完整
类型是否正确
OHLC 是否合理
成交量是否非负
成交额是否非负
```

---

### 11.5 `tests/test_minute_aggregation.py`

检查：

```text
5min 是否由 1min 正确聚合
15min 是否由 1min 正确聚合
30min 是否由 1min 正确聚合
60min 是否由 1min 正确聚合
```

---

### 11.6 `tests/test_corporate_actions.py`

检查：

```text
corporate_actions.parquet 是否存在
重大事件是否有记录
available_at 是否存在
event_type 是否合法
```

---

### 11.7 `tests/test_structural_breaks.py`

检查：

```text
structural_breaks.parquet 是否存在
regime_id 是否合法
合并断点是否记录
model_action 是否存在
```

---

### 11.8 `tests/test_data_manifest.py`

检查：

```text
data_manifest.json 是否存在
snapshot_id 是否存在
所有 processed 文件是否登记
sha256 是否存在
行数是否正确
```

---

## 12. 第一阶段 MVP

第一阶段必须完成：

```text
TUSHARE_TOKEN 配置
交易日历
中国船舶日线
中国船舶1分钟线
1min 聚合 5/15/30/60min
资金流数据
公司行为表
结构断点表
数据质量检查
数据快照
data_manifest
下游读取契约
```

第一阶段暂不做：

```text
复杂行业数据
新闻 NLP
宏观数据
同类标的自动化全覆盖
网页报告
买卖信号
模型预测
```

---

## 13. 第二阶段目标

第二阶段增加：

```text
peer_daily.parquet
index_daily.parquet
industry_daily.parquet
valuation_pit.parquet
fundamentals_pit.parquet
corporate_announcements.parquet
```

目标：

```text
支持 CNSV 做生态强弱
支持同类标的比较
支持估值和基本面情景模型
```

---

## 14. 第三阶段目标

第三阶段增加：

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

目标：

```text
支持 60D / 120D 中长期模型
支持行业周期分析
支持宏观与事件叠加
```

---

## 15. requirements.txt 建议

第一版依赖：

```text
pandas
numpy
pyarrow
tushare
python-dotenv
pydantic
pytest
```

后续可增加：

```text
duckdb
scipy
statsmodels
scikit-learn
```

第一版不建议引入过多复杂依赖。

---

## 16. README 要求

`README.md` 必须说明：

```text
CNSVdata 是什么
服务哪个主仓库
如何配置 TUSHARE_TOKEN
如何手动运行数据拉取
如何查看质量报告
哪些文件供 CNSV 读取
数据异常时如何处理
```

README 中不得出现真实 TOKEN。

---

## 17. 质量验收标准

第一阶段验收通过条件：

```text
GitHub Actions 能运行
TUSHARE_TOKEN 能通过 Secrets 读取
trade_calendar.parquet 能生成
cnsv_daily.parquet 能生成
cnsv_1min.parquet 能生成
5/15/30/60min 能从1min聚合
data_quality_latest.json 能生成
data_manifest.json 能生成
latest_trade_date.json 能生成
next_trade_date.json 能生成
tests 全部通过
```

质量报告必须达到：

```text
PASS
```

否则 CNSV 主程序不得进入正式辅助信号阶段。

---

## 18. 与 CNSV 主程序的衔接

`CNSV` 后续读取数据时，只能依赖 `CNSVdata` 的 processed、quality 和 metadata。

读取顺序：

```text
读取 metadata/latest_trade_date.json
读取 data/quality/data_quality_latest.json
如果质量为 PASS 或 WARN，再读取 processed 数据
如果质量为 FAIL，停止正式信号输出
读取 data_manifest.json，写入 CNSV 报告 provenance
```

CNSV 报告必须记录：

```text
data_snapshot_id
data_snapshot_hash
latest_trade_date
data_quality_status
```

---

## 19. 风险提示

`CNSVdata` 的错误不会直接下单，但会影响 `CNSV` 的实盘人工辅助判断。

因此数据底座必须优先保证：

```text
准确性
完整性
可回放
可审计
可追溯
时点正确
结构断点明确
```

不能为了每天跑成功而忽略数据质量。

如果数据异常，宁可输出 `FAIL`，也不能伪装成正常数据。

---

## 20. 最终结论

`CNSVdata` 是整个中国船舶实盘人工量化系统的地基。

它的核心不是“能把数据拉下来”，而是：

```text
数据能不能被信任
数据能不能被复盘
数据能不能被审计
数据能不能支撑实盘人工决策
```

只有 `CNSVdata` 稳定后，`CNSV` 主程序的价格路径预测、风险预算、仓位计划和实盘人工执行辅助才有意义。
