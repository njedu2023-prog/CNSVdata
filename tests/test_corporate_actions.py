import pandas as pd


def test_corporate_action_event_type_is_known():
    df = pd.DataFrame({"event_type": ["merger"], "available_at": ["2025-09-01"]})
    assert set(df["event_type"]) <= {"dividend", "bonus_share", "rights_issue", "ex_right", "suspension", "resumption", "share_change", "merger", "share_swap", "delisting_related", "other"}
    assert df["available_at"].notna().all()
