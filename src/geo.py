"""Great-circle distance and bounding-box math (no external deps)."""
import math

EARTH_RADIUS_MILES = 3958.8
MILES_PER_DEGREE_LAT = 69.0


def haversine_miles(lat1, lon1, lat2, lon2):
    """True great-circle distance in miles between two lat/lon points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_MILES * c


def bounding_box(lat, lon, radius_miles):
    """A lat/lon box covering at least radius_miles around (lat, lon).

    This is intentionally loose (a square, not a circle) - the OpenSky query
    uses it to cut down what's fetched, and haversine_miles() enforces the
    real radius afterwards on each candidate.
    """
    delta_lat = radius_miles / MILES_PER_DEGREE_LAT
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 1e-6:
        cos_lat = 1e-6  # avoid a divide-by-zero blowup near the poles
    delta_lon = radius_miles / (MILES_PER_DEGREE_LAT * cos_lat)

    return {
        "lamin": max(lat - delta_lat, -90.0),
        "lamax": min(lat + delta_lat, 90.0),
        "lomin": lon - delta_lon,
        "lomax": lon + delta_lon,
    }
