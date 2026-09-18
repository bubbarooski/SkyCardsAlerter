"""Plain local JSON dedupe/cooldown store - no database.

Format on disk: { "<icao24>": <unix_timestamp_last_alerted>, ... }
"""
import json
import os
import time


def load_store(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


def save_store(path, store):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)  # atomic on both POSIX and Windows


def is_on_cooldown(store, icao24, cooldown_hours, now=None):
    now = time.time() if now is None else now
    last = store.get(icao24)
    if last is None:
        return False
    return (now - last) < cooldown_hours * 3600


def mark_alerted(store, icao24, now=None):
    store[icao24] = time.time() if now is None else now
