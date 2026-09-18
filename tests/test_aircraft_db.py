import json
import os
import time

import pytest

from src import aircraft_db
from src.errors import AircraftDbError

SAMPLE_CSV = (
    "icao24,registration,manufacturericao,manufacturername,model,typecode,operator\n"
    "a1b2c3,N12345,BOEING,Boeing,787-9,B788,Test Air\n"
    "d4e5f6,N67890,AIRBUS,Airbus,A380-800,A388,Test Air\n"
    "000000,,,,,,\n"  # no typecode -> should be skipped
)


def test_build_index_from_csv(tmp_path):
    csv_path = tmp_path / "aircraftDatabase.csv"
    csv_path.write_text(SAMPLE_CSV)
    index = aircraft_db.build_index_from_csv(str(csv_path))
    assert index == {"a1b2c3": "B788", "d4e5f6": "A388"}


def _base_cfg(tmp_path, index_path):
    return {
        "aircraft_db_csv_path": str(tmp_path / "aircraftDatabase.csv"),
        "aircraft_db_index_path": str(index_path),
        "aircraft_db_max_age_days": 7,
        "aircraft_db_url": "https://example.invalid/aircraftDatabase.csv",
    }


def test_ensure_index_uses_fresh_cache_without_downloading(tmp_path, monkeypatch):
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps({"a1b2c3": "B788"}))

    def fail_download(*args, **kwargs):
        raise AssertionError("should not attempt download when cache is fresh")

    monkeypatch.setattr(aircraft_db, "download_csv", fail_download)

    index = aircraft_db.ensure_index(_base_cfg(tmp_path, index_path), log=lambda msg: None)
    assert index == {"a1b2c3": "B788"}


def test_ensure_index_falls_back_to_stale_cache_on_download_failure(tmp_path, monkeypatch):
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps({"a1b2c3": "B788"}))
    old_time = time.time() - 999999
    os.utime(index_path, (old_time, old_time))

    def fail_download(*args, **kwargs):
        raise IOError("network down")

    monkeypatch.setattr(aircraft_db, "download_csv", fail_download)

    messages = []
    index = aircraft_db.ensure_index(_base_cfg(tmp_path, index_path), log=messages.append)
    assert index == {"a1b2c3": "B788"}
    assert any("WARNING" in m for m in messages)


def test_ensure_index_raises_when_no_cache_and_download_fails(tmp_path, monkeypatch):
    def fail_download(*args, **kwargs):
        raise IOError("network down")

    monkeypatch.setattr(aircraft_db, "download_csv", fail_download)

    with pytest.raises(AircraftDbError):
        aircraft_db.ensure_index(_base_cfg(tmp_path, tmp_path / "index.json"), log=lambda m: None)


def test_ensure_index_rebuilds_when_csv_fresh_but_index_missing(tmp_path, monkeypatch):
    csv_path = tmp_path / "aircraftDatabase.csv"
    csv_path.write_text(SAMPLE_CSV)
    index_path = tmp_path / "index.json"

    def fail_download(*args, **kwargs):
        raise AssertionError("should not re-download when csv is already fresh")

    monkeypatch.setattr(aircraft_db, "download_csv", fail_download)

    index = aircraft_db.ensure_index(_base_cfg(tmp_path, index_path), log=lambda m: None)
    assert index == {"a1b2c3": "B788", "d4e5f6": "A388"}
