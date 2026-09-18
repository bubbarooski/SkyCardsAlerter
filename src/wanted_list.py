"""Loads the user-maintained 'still need for Skycards' aircraft list."""
import json
import os

from .errors import SkyCardsError


class WantedListError(SkyCardsError):
    pass


def load_wanted_list(path):
    """Returns {ICAO_TYPE: model_name} for every entry with a type code."""
    if not os.path.exists(path):
        raise WantedListError(
            f"Wanted list not found at '{path}'. Copy data/wanted_list.json.example "
            f"to {path} and fill in the aircraft you're after."
        )
    with open(path, "r", encoding="utf-8") as f:
        try:
            entries = json.load(f)
        except json.JSONDecodeError as e:
            raise WantedListError(f"Wanted list '{path}' is not valid JSON: {e}") from e

    wanted = {}
    for entry in entries:
        icao_type = str(entry.get("icao_type", "")).strip().upper()
        model_name = str(entry.get("model_name", "")).strip()
        if not icao_type:
            continue
        wanted[icao_type] = model_name or icao_type
    return wanted
