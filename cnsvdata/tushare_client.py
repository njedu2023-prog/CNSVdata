import os
import time
from collections.abc import Callable

from cnsvdata.common import load_yaml


def get_tushare_pro():
    config = load_yaml("tushare.yml")["tushare"]
    token = os.getenv(config["token_env"])
    if not token:
        raise RuntimeError(f"{config['token_env']} is not configured")

    import tushare as ts

    ts.set_token(token)
    return ts.pro_api(token)


def call_with_retry(fn: Callable, retry_times: int = 3, sleep_seconds: int = 5, **kwargs):
    last_error = None
    for attempt in range(retry_times):
        try:
            return fn(**kwargs)
        except Exception as exc:
            last_error = exc
            if attempt < retry_times - 1:
                time.sleep(sleep_seconds)
    raise last_error
