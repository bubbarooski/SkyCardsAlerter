"""City lookup table: maps a command-line flag to center coordinates.

Adding a new city is just adding an entry here - no other code changes
needed. Only well-known public city coordinates belong here (see CLAUDE.md /
skycards-alert-bot-spec.md on why: this repo is public).
"""
from .errors import CityError

CITIES = {
    "jacksonvilleFL": {"label": "Jacksonville, FL", "lat": 30.3322, "lon": -81.6557},
    "miamiFL": {"label": "Miami, FL", "lat": 25.7617, "lon": -80.1918},
    "orlandoFL": {"label": "Orlando, FL", "lat": 28.5383, "lon": -81.3792},
    "atlantaGA": {"label": "Atlanta, GA", "lat": 33.7490, "lon": -84.3880},
    "nycNY": {"label": "New York, NY", "lat": 40.7128, "lon": -74.0060},
    "losangelesCA": {"label": "Los Angeles, CA", "lat": 34.0522, "lon": -118.2437},
    "chicagoIL": {"label": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
    "dallasTX": {"label": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
    "londonUK": {"label": "London, UK", "lat": 51.5072, "lon": -0.1276},
    "istanbulTUR": {"label": "Istanbul, Turkey", "lat": 41.0082, "lon": 28.9784},
    "dubaiUAE": {"label": "Dubai, UAE", "lat": 25.2048, "lon": 55.2708},
    "singaporeSG": {"label": "Singapore", "lat": 1.3521, "lon": 103.8198},
}

DEFAULT_CITY_KEY = "jacksonvilleFL"


def get_city(key):
    """Look up a city by its flag key (no leading dash). Returns (key, city_dict)."""
    if key not in CITIES:
        available = ", ".join(sorted(CITIES))
        raise CityError(f"Unknown city flag '{key}'. Available: {available}")
    return key, CITIES[key]
