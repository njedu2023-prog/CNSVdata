from cnsvdata.daily import daily_downstream_contract


def test_daily_contract_disables_intraday_and_formal_signal():
    contract = daily_downstream_contract({"ready": True})

    assert contract["line"] == "daily"
    assert contract["can_run_daily_model"] is True
    assert contract["can_run_intraday_model"] is False
    assert contract["can_generate_formal_signal"] is False
