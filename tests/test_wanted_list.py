import json

import pytest

from src import wanted_list
from src.errors import SkyCardsError


def test_load_wanted_list(tmp_path):
    path = tmp_path / "wanted.json"
    path.write_text(json.dumps([
        {"model_name": "Boeing 787", "icao_type": "b788"},
        {"model_name": "Airbus A380", "icao_type": "A388"},
    ]))
    wanted = wanted_list.load_wanted_list(str(path))
    assert wanted == {"B788": "Boeing 787", "A388": "Airbus A380"}


def test_entries_without_icao_type_are_skipped(tmp_path):
    path = tmp_path / "wanted.json"
    path.write_text(json.dumps([{"model_name": "Mystery Plane", "icao_type": ""}]))
    assert wanted_list.load_wanted_list(str(path)) == {}


def test_missing_file_raises(tmp_path):
    with pytest.raises(SkyCardsError):
        wanted_list.load_wanted_list(str(tmp_path / "missing.json"))


def test_invalid_json_raises(tmp_path):
    path = tmp_path / "wanted.json"
    path.write_text("{not json")
    with pytest.raises(SkyCardsError):
        wanted_list.load_wanted_list(str(path))
