# CNSVdata Failure Summary

## Overall Status

FAIL

- Failed count: 5
- Warning count: 0

## Blocking

true

- Blocking reason: latest_trade_date_consistency failed

## Can CNSV Main Start?

NO

## Top Failures

### 1. latest_trade_date_consistency

- Source: quality
- Status: FAIL
- Detail: daily or metadata latest date mismatch
- Suggested action: rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks

### 2. latest_trade_date_consistency

- Source: acceptance
- Status: FAIL
- Detail: daily latest date mismatch
- Suggested action: rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks

### 3. quality_status

- Source: acceptance
- Status: FAIL
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 4. quality_not_fail

- Source: smoke
- Status: FAIL
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 5. acceptance_not_fail

- Source: smoke
- Status: FAIL
- Detail: 
- Suggested action: inspect the source report and rerun the affected data pipeline step

## Top Warnings

None
## Concrete Missing Dates

None

## Suggested Backfill Commands

None

## Minute Backfill Plan

- SOP: `docs/minute_backfill_sop.md`
- Decision: not_required_for_current_readiness
- Reason: minute active coverage window is complete enough for current downstream readiness; historical gaps remain informational.
- Coverage scope: available_window:2026-06-09..2026-06-18
- Active missing trade dates: 0
- Historical missing count: 3987
- Command when required: `python scripts/backfill_missing_data.py --minute`

## Allowed Usage

- Develop CNSV main program: NO
- Run daily ingest: NO
- Run backtest/training: NO
- Use moneyflow as strong factor: NO
- Generate formal signal: NO

## Next Action

rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks
