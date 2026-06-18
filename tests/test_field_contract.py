import pandas as pd

from cnsvdata.common import load_yaml
from cnsvdata.validators import field_contract_checks


def test_field_contract_can_load():
    contract = load_yaml("field_contract.yml")["contract"]
    assert contract["version"] == "1.2.0"
    assert "cnsv_daily" in contract["datasets"]


def test_field_contract_flags_missing_required_field():
    contract = load_yaml("field_contract.yml")["contract"]["datasets"]["cnsv_daily"]
    checks = field_contract_checks(pd.DataFrame({"trade_date": ["2026-06-18"]}), "cnsv_daily", contract)
    assert any(check["status"] == "FAIL" for check in checks)
