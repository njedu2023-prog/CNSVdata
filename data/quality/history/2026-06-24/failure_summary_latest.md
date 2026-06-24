# CNSVdata Failure Summary

## Overall Status

PASS

- Failed count: 0
- Warning count: 0

## Blocking

false

- Blocking reason: None

## Can CNSV Main Start?

YES

## Top Failures

None
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
- Coverage scope: available_window:2026-06-09..2026-06-24
- Active missing trade dates: 0
- Historical missing count: 3987
- Command when required: `python scripts/backfill_missing_data.py --minute`

## Allowed Usage

- Develop CNSV main program: YES
- Run daily ingest: YES
- Run backtest/training: YES
- Use moneyflow as strong factor: YES
- Generate formal signal: NO

## Next Action

start CNSV main program connection development with formal-signal gate disabled and minute backfill SOP documented
