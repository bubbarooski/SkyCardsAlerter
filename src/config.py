"""Loads config.json (gitignored - real secrets) with defaults filled in."""
import json
import os

from .errors import ConfigError

DEFAULT_CONFIG = {
    "ntfy_topic": "",
    "radius_miles": 100,
    "cooldown_hours": 2,
    "default_city": "jacksonvilleFL",
    "wanted_list_path": "data/wanted_list.json",
    "dedupe_store_path": "data/dedupe_store.json",
    "aircraft_db_csv_path": "data/aircraftDatabase.csv",
    "aircraft_db_index_path": "data/aircraft_type_index.json",
    "aircraft_db_max_age_days": 7,
    "aircraft_db_url": "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv",
    "opensky_client_id": "",
    "opensky_client_secret": "",
    "request_timeout_seconds": 20,
}


def load_config(path="config.json"):
    if not os.path.exists(path):
        raise ConfigError(
            f"Config file not found at '{path}'. Copy config.example.json to "
            f"{path} and fill in your ntfy topic before running."
        )
    with open(path, "r", encoding="utf-8") as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Config file '{path}' is not valid JSON: {e}") from e

    cfg = dict(DEFAULT_CONFIG)
    cfg.update(raw)
    return cfg
