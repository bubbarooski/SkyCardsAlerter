"""OpenSky Network client: OAuth2 client-credentials auth (optional) + /states/all."""
import requests

from .errors import OpenSkyError

STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/"
    "protocol/openid-connect/token"
)

# Indexes into each raw OpenSky state vector row.
_IDX_ICAO24 = 0
_IDX_CALLSIGN = 1
_IDX_LON = 5
_IDX_LAT = 6
_IDX_BARO_ALT = 7
_IDX_ON_GROUND = 8
_IDX_VELOCITY = 9


def _get_access_token(client_id, client_secret, timeout):
    try:
        resp = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        raise OpenSkyError(f"Failed to authenticate with OpenSky: {e}") from e


def fetch_states(bbox, cfg):
    """Fetches live state vectors within bbox, returns a list of parsed dicts."""
    timeout = cfg.get("request_timeout_seconds", 20)
    headers = {}
    client_id = cfg.get("opensky_client_id")
    client_secret = cfg.get("opensky_client_secret")
    if client_id and client_secret:
        token = _get_access_token(client_id, client_secret, timeout)
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "lamin": bbox["lamin"],
        "lomin": bbox["lomin"],
        "lamax": bbox["lamax"],
        "lomax": bbox["lomax"],
    }
    try:
        resp = requests.get(STATES_URL, params=params, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        raise OpenSkyError(f"Network error contacting OpenSky: {e}") from e

    if resp.status_code == 429:
        raise OpenSkyError("OpenSky rate limit hit (HTTP 429). Back off and try again later.")
    if resp.status_code != 200:
        raise OpenSkyError(f"OpenSky returned HTTP {resp.status_code}: {resp.text[:200]}")

    try:
        payload = resp.json()
    except ValueError as e:
        raise OpenSkyError(f"OpenSky returned invalid JSON: {e}") from e

    return [parsed for parsed in (_parse_row(row) for row in payload.get("states") or []) if parsed]


def _parse_row(row):
    try:
        icao24 = (row[_IDX_ICAO24] or "").strip().lower()
        lat = row[_IDX_LAT]
        lon = row[_IDX_LON]
    except (IndexError, TypeError):
        return None
    if not icao24 or lat is None or lon is None:
        return None
    return {
        "icao24": icao24,
        "callsign": (row[_IDX_CALLSIGN] or "").strip(),
        "lat": lat,
        "lon": lon,
        "altitude_m": row[_IDX_BARO_ALT],
        "on_ground": bool(row[_IDX_ON_GROUND]),
        "velocity_ms": row[_IDX_VELOCITY],
    }
