import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_parquet
from cnsvdata.paths import DATA_DIR, PROCESSED_DIR

SCHEMA = ["regime_id", "start_date", "end_date", "description", "reason", "impact_fields", "model_action", "created_at"]


def main() -> None:
    created_at = now_string()
    rows = load_yaml("manual_structural_breaks.yml").get("regimes", [])
    df = pd.DataFrame(rows, columns=[column for column in SCHEMA if column != "created_at"])
    if df.empty:
        df = pd.DataFrame(columns=SCHEMA)
    df["created_at"] = created_at
    write_parquet(df[SCHEMA], PROCESSED_DIR / "structural_breaks.parquet")
    write_parquet(df[SCHEMA], DATA_DIR / "daily" / "processed" / "structural_breaks.parquet")


if __name__ == "__main__":
    main()
