from src import dedupe


def test_no_cooldown_when_never_alerted():
    assert not dedupe.is_on_cooldown({}, "abc123", 2, now=1000)


def test_cooldown_active_within_window():
    store = {}
    dedupe.mark_alerted(store, "abc123", now=1000)
    assert dedupe.is_on_cooldown(store, "abc123", 2, now=1000 + 3600)


def test_cooldown_expires_after_window():
    store = {}
    dedupe.mark_alerted(store, "abc123", now=1000)
    assert not dedupe.is_on_cooldown(store, "abc123", 2, now=1000 + 3 * 3600)


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "dedupe_store.json")
    store = {"abc123": 1234.5}
    dedupe.save_store(path, store)
    assert dedupe.load_store(path) == store


def test_load_missing_file_returns_empty(tmp_path):
    assert dedupe.load_store(str(tmp_path / "nope.json")) == {}


def test_load_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not valid json")
    assert dedupe.load_store(str(path)) == {}
