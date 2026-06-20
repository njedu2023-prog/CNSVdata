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

### 6. cnsv_1min.parquet_exists

- Source: quality
- Status: FAIL
- Detail: missing file
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 7. field_contract:cnsv_1min:readable

- Source: quality
- Status: FAIL
- Detail: dataset_not_readable
- Suggested action: inspect the source report and rerun the affected data pipeline step

### 8. field_contract:cnsv_moneyflow:nullable

- Source: quality
- Status: FAIL
- Detail: 
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

### 9. moneyflow_core_nulls

- Source: quality
- Status: FAIL
- Detail: 
- Suggested action: rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks

### 10. required_file:data/processed/cnsv_1min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 11. required_file:data/processed/cnsv_5min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 12. required_file:data/processed/cnsv_15min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 13. required_file:data/processed/cnsv_30min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 14. required_file:data/processed/cnsv_60min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 15. parquet_readable:cnsv_1min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 16. parquet_readable:cnsv_5min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 17. parquet_readable:cnsv_15min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 18. parquet_readable:cnsv_30min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 19. parquet_readable:cnsv_60min.parquet

- Source: acceptance
- Status: FAIL
- Detail: missing
- Suggested action: run detect_data_gaps and backfill_missing_data for the affected dataset

### 20. latest_trade_date_consistency

- Source: acceptance
- Status: FAIL
- Detail: minute latest date mismatch
- Suggested action: rerun fetch_minute, build_minute_bars, quality, acceptance, and smoke checks

## Top Warnings

None
