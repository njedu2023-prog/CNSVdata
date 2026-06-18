from pathlib import Path

from cnsvdata.common import load_yaml


def test_data_contract_required_files_are_safe_relative_paths():
    contract = load_yaml("data_contract.yml")["contract"]
    required = contract["required_files"]
    assert required
    for item in required:
        path = Path(item)
        assert not path.is_absolute()
        assert ".." not in path.parts
