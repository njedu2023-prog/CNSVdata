# CNSVdata Failure Summary

## Overall Status

FAIL

## Blocking

true

## Top Failures

### 1. required_file:data/processed/cnsv_1min.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 2. required_file:data/processed/cnsv_5min.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 3. required_file:data/processed/cnsv_15min.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 4. required_file:data/processed/cnsv_30min.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 5. required_file:data/processed/cnsv_60min.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 6. required_file:data/processed/corporate_actions.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 7. required_file:data/processed/structural_breaks.parquet

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 8. required_file:metadata/data_manifest.json

- Source: quality
- Status: FAIL
- Detail: missing
- Suggested action: rerun build_data_manifest after source data and quality reports are updated

### 9. cnsv_1min.parquet_exists

- Source: quality
- Status: FAIL
- Detail: missing file
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 10. corporate_actions.parquet_exists

- Source: quality
- Status: FAIL
- Detail: missing file
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 11. structural_breaks.parquet_exists

- Source: quality
- Status: FAIL
- Detail: missing file
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 12. field_contract:cnsv_1min:readable

- Source: quality
- Status: FAIL
- Detail: dataset_not_readable
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 13. field_contract:cnsv_moneyflow:nullable

- Source: quality
- Status: FAIL
- Detail: 
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

### 14. moneyflow_core_nulls

- Source: quality
- Status: FAIL
- Detail: 
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

### 15. required_file:data/processed/cnsv_1min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 16. required_file:data/processed/cnsv_5min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 17. required_file:data/processed/cnsv_15min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 18. required_file:data/processed/cnsv_30min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 19. required_file:data/processed/cnsv_60min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 20. required_file:data/processed/corporate_actions.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

## Top Warnings

### 1. daily_missing_trade_dates

- Source: gaps
- Status: WARN
- Detail: historical_gaps_detected
- Suggested action: rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks
