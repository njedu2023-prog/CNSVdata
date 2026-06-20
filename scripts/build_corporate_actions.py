import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_parquet
from cnsvdata.paths import DATA_DIR, PROCESSED_DIR

SCHEMA = ["ts_code", "event_date", "available_at", "event_type", "event_name", "description", "raw_source", "impact_level", "created_at"]

SCHEMA = ["ts_code", "event_date", "available_at", "event_type", "event_name", "description", "raw_source", "impact_level", "created_at"]


def main() -> None:
    created_at = now_string()
    rows = load_yaml("manual_corporate_actions.yml").get("events", [])
    df = pd.DataFrame(rows, columns=[column for column in SCHEMA if column != "created_at"])
    if df.empty:
        df = pd.DataFrame(columns=SCHEMA)
    df["created_at"] = created_at
    df = df[SCHEMA]
    write_parquet(df, PROCESSED_DIR / "corporate_actions.parquet")
    write_parquet(df, DATA_DIR / "daily" / "processed" / "corporate_actions.parquet")


if __name__ == "__main__":
    main()
