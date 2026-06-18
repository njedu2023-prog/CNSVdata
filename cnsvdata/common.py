import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

from cnsvdata.paths import CONFIG_DIR

TZ = "Asia/Shanghai"


def now_string() -> str:
    return datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d %H:%M:%S")


def load_yaml(name: str) -> dict:
    with (CONFIG_DIR / name).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_trade_date(value: str) -> str:
    text = str(value)
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text
