import requests

from src import notify


class FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


def test_build_fr24_link():
    assert notify.build_fr24_link("UAL 123") == "https://www.flightradar24.com/UAL123"
    assert notify.build_fr24_link("") is None
    assert notify.build_fr24_link(None) is None


def test_send_ntfy_success(monkeypatch):
    captured = {}

    def fake_post(url, data=None, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["data"] = data
        return FakeResponse(200)

    monkeypatch.setattr(notify.requests, "post", fake_post)
    ok = notify.send_ntfy("my-topic", "Title", "Body text", click_url="https://example.com")
    assert ok is True
    assert captured["url"] == "https://ntfy.sh/my-topic"
    assert captured["headers"]["Title"] == "Title"
    assert captured["headers"]["Click"] == "https://example.com"


def test_send_ntfy_no_topic_configured():
    messages = []
    ok = notify.send_ntfy("", "Title", "Body", log=messages.append)
    assert ok is False
    assert any("WARNING" in m for m in messages)


def test_send_ntfy_handles_request_failure(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(notify.requests, "post", fake_post)
    messages = []
    ok = notify.send_ntfy("topic", "Title", "Body", log=messages.append)
    assert ok is False
    assert any("WARNING" in m for m in messages)


def test_send_ntfy_handles_bad_status(monkeypatch):
    def fake_post(url, data=None, headers=None, timeout=None):
        return FakeResponse(500, text="server error")

    monkeypatch.setattr(notify.requests, "post", fake_post)
    messages = []
    ok = notify.send_ntfy("topic", "Title", "Body", log=messages.append)
    assert ok is False
    assert any("WARNING" in m for m in messages)
