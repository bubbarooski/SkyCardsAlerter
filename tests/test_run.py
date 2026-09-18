import json

import run as run_module
from src import notify, opensky


def _make_config(tmp_path):
    wanted_path = tmp_path / "wanted_list.json"
    dedupe_path = tmp_path / "dedupe_store.json"
    csv_path = tmp_path / "aircraftDatabase.csv"
    index_path = tmp_path / "index.json"
    cfg_path = tmp_path / "config.json"

    wanted_path.write_text(json.dumps([{"model_name": "Boeing 787", "icao_type": "B788"}]))
    index_path.write_text(json.dumps({"a1b2c3": "B788", "ffffff": "A320"}))

    cfg = {
        "ntfy_topic": "test-topic",
        "radius_miles": 100,
        "cooldown_hours": 2,
        "default_city": "jacksonvilleFL",
        "wanted_list_path": str(wanted_path),
        "dedupe_store_path": str(dedupe_path),
        "aircraft_db_csv_path": str(csv_path),
        "aircraft_db_index_path": str(index_path),
        "aircraft_db_max_age_days": 7,
        "aircraft_db_url": "https://example.invalid/db.csv",
        "opensky_client_id": "",
        "opensky_client_secret": "",
        "request_timeout_seconds": 5,
    }
    cfg_path.write_text(json.dumps(cfg))
    return str(cfg_path)


def _state(icao24="a1b2c3", callsign="UAL123", lat=30.40, lon=-81.60):
    return {
        "icao24": icao24,
        "callsign": callsign,
        "lat": lat,
        "lon": lon,
        "altitude_m": 1000,
        "on_ground": False,
        "velocity_ms": 200,
    }


def test_full_run_sends_one_notification_then_suppresses_on_cooldown(tmp_path, monkeypatch):
    cfg_path = _make_config(tmp_path)

    monkeypatch.setattr(opensky, "fetch_states", lambda bbox, cfg: [_state()])

    sent = []

    def fake_send_ntfy(topic, title, message, click_url=None, timeout=20, log=print):
        sent.append((topic, title, message))
        return True

    monkeypatch.setattr(notify, "send_ntfy", fake_send_ntfy)

    assert run_module.run(["-jacksonvilleFL", "--config", cfg_path]) == 0
    assert len(sent) == 1

    # Same aircraft again immediately after - cooldown should suppress the repeat push.
    assert run_module.run(["-jacksonvilleFL", "--config", cfg_path]) == 0
    assert len(sent) == 1


def test_run_skips_aircraft_outside_radius(tmp_path, monkeypatch):
    cfg_path = _make_config(tmp_path)
    far_away = _state(callsign="UAL999", lat=47.0, lon=-122.0)
    monkeypatch.setattr(opensky, "fetch_states", lambda bbox, cfg: [far_away])

    sent = []
    monkeypatch.setattr(notify, "send_ntfy", lambda *a, **k: sent.append(1) or True)

    assert run_module.run(["-jacksonvilleFL", "--config", cfg_path]) == 0
    assert sent == []


def test_run_skips_non_wanted_type(tmp_path, monkeypatch):
    cfg_path = _make_config(tmp_path)
    non_wanted = _state(icao24="ffffff", callsign="DAL456")  # maps to A320, not wanted
    monkeypatch.setattr(opensky, "fetch_states", lambda bbox, cfg: [non_wanted])

    sent = []
    monkeypatch.setattr(notify, "send_ntfy", lambda *a, **k: sent.append(1) or True)

    assert run_module.run(["-jacksonvilleFL", "--config", cfg_path]) == 0
    assert sent == []


def test_run_reports_error_on_missing_config():
    assert run_module.run(["--config", "does-not-exist.json"]) == 1


def test_run_help_flag_returns_zero(capsys):
    assert run_module.run(["--help"]) == 0
    out = capsys.readouterr().out
    assert "jacksonvilleFL" in out
