# CNSVdata Failure Summary

## Overall Status

WARN

- Failed count: 0
- Warning count: 9

## Blocking

false

- Blocking reason: None

## Can CNSV Main Start?

YES

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

### 3. data_gaps_status

- Source: acceptance
- Status: WARN
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 4. quality_not_fail

- Source: smoke
- Status: WARN
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 5. acceptance_not_fail

- Source: smoke
- Status: WARN
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 6. daily_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: historical_gaps_detected
- Suggested action: rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks

### 7. minute_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: historical_gaps_detected
- Suggested action: rerun fetch_minute, build_minute_bars, quality, acceptance, and smoke checks

### 8. minute_missing_minutes

- Source: gaps
- Status: WARN
- Detail: 
- Suggested action: rerun fetch_minute, build_minute_bars, quality, acceptance, and smoke checks

### 9. moneyflow_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: latest_or_historical_gaps_detected
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

## Concrete Missing Dates

- daily: 2010-05-20, 2010-08-19, 2011-02-18, 2011-02-21, 2011-02-22, 2011-02-23, 2011-02-24, 2011-02-25, 2011-02-28, 2011-03-01, 2011-03-02, 2011-03-03, 2011-05-10, 2011-06-23, 2012-05-25, 2017-09-27, 2017-09-28, 2017-09-29, 2017-10-09, 2017-10-10, 2017-10-11, 2017-10-12, 2017-10-13, 2017-10-16, 2017-10-17, 2017-10-18, 2017-10-19, 2017-10-20, 2017-10-23, 2017-10-24
- minute: 2010-01-04, 2010-01-05, 2010-01-06, 2010-01-07, 2010-01-08, 2010-01-11, 2010-01-12, 2010-01-13, 2010-01-14, 2010-01-15, 2010-01-18, 2010-01-19, 2010-01-20, 2010-01-21, 2010-01-22, 2010-01-25, 2010-01-26, 2010-01-27, 2010-01-28, 2010-01-29, 2010-02-01, 2010-02-02, 2010-02-03, 2010-02-04, 2010-02-05, 2010-02-08, 2010-02-09, 2010-02-10, 2010-02-11, 2010-02-12
- moneyflow: 2010-05-20, 2010-08-19, 2011-02-18, 2011-02-21, 2011-02-22, 2011-02-23, 2011-02-24, 2011-02-25, 2011-02-28, 2011-03-01, 2011-03-02, 2011-03-03, 2011-05-10, 2011-06-23, 2012-05-25, 2017-09-27, 2017-09-28, 2017-09-29, 2017-10-09, 2017-10-10, 2017-10-11, 2017-10-12, 2017-10-13, 2017-10-16, 2017-10-17, 2017-10-18, 2017-10-19, 2017-10-20, 2017-10-23, 2017-10-24

## Suggested Backfill Commands

- `python scripts/backfill_missing_data.py --from-gap-report`
- `python scripts/backfill_missing_data.py --daily`
- `python scripts/backfill_missing_data.py --minute`
- `python scripts/backfill_missing_data.py --moneyflow`

## Allowed Usage

- Develop CNSV main program: YES
- Run daily ingest: YES
- Run backtest/training: NO
- Use moneyflow as strong factor: NO
- Generate formal signal: NO

## Next Action

review WARN impacts, run suggested backfills when source data becomes available, then rerun acceptance
