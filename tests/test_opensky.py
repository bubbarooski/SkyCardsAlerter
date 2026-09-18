import pytest
import requests

from src import opensky
from src.errors import OpenSkyError


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _cfg(**overrides):
    cfg = {"request_timeout_seconds": 5, "opensky_client_id": "", "opensky_client_secret": ""}
    cfg.update(overrides)
    return cfg


def test_fetch_states_parses_valid_response(monkeypatch):
    payload = {
        "states": [
            ["a1b2c3", "UAL123  ", "United States", None, None,
             -81.5, 30.3, 1000, False, 200, 90, 0, None, 1000, None, False, 0],
            [None, None, None, None, None, None, None, None, None,
             None, None, None, None, None, None, None, None],
        ]
    }

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(200, payload)

    monkeypatch.setattr(opensky.requests, "get", fake_get)

    bbox = {"lamin": 0, "lomin": 0, "lamax": 1, "lomax": 1}
    states = opensky.fetch_states(bbox, _cfg())
    assert len(states) == 1
    assert states[0]["icao24"] == "a1b2c3"
    assert states[0]["callsign"] == "UAL123"


def test_fetch_states_raises_on_rate_limit(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(429, {}, text="slow down")

    monkeypatch.setattr(opensky.requests, "get", fake_get)

    bbox = {"lamin": 0, "lomin": 0, "lamax": 1, "lomax": 1}
    with pytest.raises(OpenSkyError):
        opensky.fetch_states(bbox, _cfg())


def test_fetch_states_raises_on_network_error(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr(opensky.requests, "get", fake_get)

    bbox = {"lamin": 0, "lomin": 0, "lamax": 1, "lomax": 1}
    with pytest.raises(OpenSkyError):
        opensky.fetch_states(bbox, _cfg())


def test_fetch_states_uses_oauth_token_when_configured(monkeypatch):
    calls = {}

    def fake_post(url, data=None, timeout=None):
        calls["token_requested"] = True
        return FakeResponse(200, {"access_token": "tok123"})

    def fake_get(url, params=None, headers=None, timeout=None):
        calls["headers"] = headers
        return FakeResponse(200, {"states": []})

    monkeypatch.setattr(opensky.requests, "post", fake_post)
    monkeypatch.setattr(opensky.requests, "get", fake_get)

    bbox = {"lamin": 0, "lomin": 0, "lamax": 1, "lomax": 1}
    cfg = _cfg(opensky_client_id="id", opensky_client_secret="secret")
    opensky.fetch_states(bbox, cfg)
    assert calls["token_requested"]
    assert calls["headers"]["Authorization"] == "Bearer tok123"
