# CNSVdata Failure Summary

## Overall Status

FAIL

## Blocking

true

## Top Failures

### 1. missing_report:data/quality/data_quality_latest.json

- Source: quality
- Status: FAIL
- Detail: report file is missing
- Suggested action: rerun the acceptance workflow from the beginning

### 2. missing_report:data/quality/acceptance_latest.json

- Source: acceptance
- Status: FAIL
- Detail: report file is missing
- Suggested action: rerun the acceptance workflow from the beginning

### 3. missing_report:data/quality/downstream_smoke_latest.json

- Source: smoke
- Status: FAIL
- Detail: report file is missing
- Suggested action: rerun the acceptance workflow from the beginning

### 4. daily_missing_trade_dates

- Source: gaps
- Status: FAIL
- Detail: latest_trade_date_missing
- Suggested action: rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks

### 5. minute_missing_trade_dates

- Source: gaps
- Status: FAIL
- Detail: latest_trade_date_missing
- Suggested action: rerun fetch_minute, build_minute_bars, quality, acceptance, and smoke checks

### 6. moneyflow_missing_trade_dates

- Source: gaps
- Status: FAIL
- Detail: too_many_missing_dates
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

## Top Warnings

None
