import pandas as pd

from cnsvdata.common import now_string, write_parquet
from cnsvdata.paths import PROCESSED_DIR


def main() -> None:
    created_at = now_string()
    rows = [
        {
            "regime_id": "legacy_cssc_before_merger",
            "start_date": "2010-01-01",
            "end_date": "2025-08-31",
            "description": "合并前中国船舶",
            "reason": "Pre-merger operating regime.",
            "impact_fields": "share_capital,market_cap,turnover_rate,amount,valuation,financial_statement,peer_pool",
            "model_action": "reduce_confidence",
            "created_at": created_at,
        },
        {
            "regime_id": "merger_transition",
            "start_date": "2025-09-01",
            "end_date": "2026-12-31",
            "description": "吸收合并过渡期",
            "reason": "Major merger integration period.",
            "impact_fields": "share_capital,market_cap,turnover_rate,amount,valuation,financial_statement,peer_pool",
            "model_action": "disable_high_confidence_signal",
            "created_at": created_at,
        },
        {
            "regime_id": "combined_cssc_after_merger",
            "start_date": "2027-01-01",
            "end_date": "",
            "description": "合并后中国船舶",
            "reason": "Post-merger combined entity regime.",
            "impact_fields": "share_capital,market_cap,turnover_rate,amount,valuation,financial_statement,peer_pool",
            "model_action": "recalibrate_model",
            "created_at": created_at,
        },
    ]
    write_parquet(pd.DataFrame(rows), PROCESSED_DIR / "structural_breaks.parquet")


if __name__ == "__main__":
    main()
