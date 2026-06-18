# CNSVdata Failure Summary

## Overall Status

WARN

## Blocking

false

## Top Failures

None
## Top Warnings

### 1. moneyflow_core_nulls

- Source: quality
- Status: WARN
- Detail: historical_or_latest_moneyflow_nulls
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

### 2. quality_status

- Source: acceptance
- Status: WARN
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 3. quality_not_fail

- Source: smoke
- Status: WARN
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 4. acceptance_not_fail

- Source: smoke
- Status: WARN
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 5. daily_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: historical_gaps_detected
- Suggested action: rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks

### 6. minute_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: historical_gaps_detected
- Suggested action: rerun fetch_minute, build_minute_bars, quality, acceptance, and smoke checks

### 7. moneyflow_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: latest_or_historical_gaps_detected
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks
