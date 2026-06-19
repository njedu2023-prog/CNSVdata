# Minute Backfill SOP

This SOP defines how CNSVdata handles minute gaps after `data_gaps_latest.json` is generated.

## Current Decision

As of the latest quality snapshot, minute data is ready for downstream development when all conditions below are true:

```text
data_gaps_latest.status = PASS
minute.status = PASS
minute_missing_trade_dates.missing_count = 0
minute_missing_minutes.coverage_ratio >= 0.99
metadata/downstream_ready.ready = true
```

Historical minute gaps, such as the full-calendar count recorded in `historical_reference.minute_missing_count`, are informational only. They do not block daily ingest, main program connection work, or current-window downstream reads.

## Gap Classification

```text
active missing trade dates   -> must be fixed before current downstream use
latest trade date missing    -> FAIL, must rerun fetch_minute and build_minute_bars
coverage_ratio < 0.99        -> WARN/FAIL depending on upstream report, run minute backfill
historical_reference gaps    -> document only unless formal backtest/training requires the period
single tolerated intraday bar -> PASS when coverage_ratio >= 0.99
```

## Backfill Requirement

Run minute backfill only when one of these is true:

```text
minute.status != PASS
minute_missing_trade_dates.missing_count > 0
minute_missing_minutes.coverage_ratio < 0.99
formal backtest/training requires a historical date range that is listed under historical_reference
```

If the only remaining item is `historical_reference.minute_missing_count`, do not treat it as a current quality defect. Record the required historical range first, then backfill that range explicitly.

## Commands

For active current-window minute defects:

```bash
python scripts/backfill_missing_data.py --from-gap-report
python scripts/backfill_missing_data.py --minute
```

For an explicit historical minute range:

```bash
python scripts/backfill_missing_data.py --start-date 20260601 --end-date 20260618 --minute
```

After any minute backfill:

```bash
python scripts/build_minute_bars.py
python scripts/build_data_manifest.py
python scripts/detect_data_gaps.py
python scripts/quality_check.py
python scripts/acceptance_check.py
python scripts/smoke_downstream_read.py
python scripts/build_downstream_ready.py
python scripts/build_failure_summary.py
```

## Formal Signal Gate

CNSVdata does not generate formal signals. Downstream systems must treat `allowed_usage.can_generate_formal_signal = false` as a hard lock.

The CNSV main repository CI should reject formal signal generation unless all of these are true:

```text
metadata/downstream_ready.ready = true
metadata/downstream_ready.status = PASS
metadata/downstream_ready.allowed_usage.can_generate_formal_signal = true
```

At the current contract stage, `can_generate_formal_signal` remains false by design. This is not a quality failure; it is a downstream safety gate.
