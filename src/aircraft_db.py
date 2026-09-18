"""Aircraft ICAO24 -> type-code lookup, backed by OpenSky's metadata CSV.

The raw CSV has ~30 columns and hundreds of thousands of rows, which is slow
to re-parse every 5-minute cron tick. So we parse it once per refresh cycle
into a small {icao24: typecode} JSON index and read that on every run
instead. Still "no database" per the project constraints - it's just a
derived cache file.
"""
import csv
import json
import os
import time

import requests

from .errors import AircraftDbError


def _file_is_fresh(path, max_age_days):
    if not os.path.exists(path):
        return False
    age_seconds = time.time() - os.path.getmtime(path)
    return age_seconds < max_age_days * 86400


def download_csv(url, dest_path, timeout=120):
    directory = os.path.dirname(dest_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp_path = f"{dest_path}.tmp"
    with requests.get(url, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    os.replace(tmp_path, dest_path)


def build_index_from_csv(csv_path):
    index = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao24 = (row.get("icao24") or "").strip().lower()
            typecode = (row.get("typecode") or "").strip().upper()
            if icao24 and typecode:
                index[icao24] = typecode
    return index


def save_index(index_path, index):
    directory = os.path.dirname(index_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp_path = f"{index_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(index, f)
    os.replace(tmp_path, index_path)


def load_index(index_path):
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_index(cfg, log=print):
    """Returns a fresh (or best-available) {icao24: typecode} index.

    Refreshes from the CSV (downloading it first if needed) when the cached
    index is missing or stale. If a refresh attempt fails but an old index
    is still on disk, warns and falls back to it rather than failing the
    whole poll cycle over a database staleness issue.
    """
    csv_path = cfg["aircraft_db_csv_path"]
    index_path = cfg["aircraft_db_index_path"]
    max_age_days = cfg["aircraft_db_max_age_days"]
    url = cfg["aircraft_db_url"]

    if _file_is_fresh(index_path, max_age_days):
        return load_index(index_path)

    try:
        if not _file_is_fresh(csv_path, max_age_days):
            log(f"Aircraft database missing or stale, downloading from {url} ...")
            download_csv(url, csv_path)
        index = build_index_from_csv(csv_path)
        save_index(index_path, index)
        return index
    except Exception as e:
        if os.path.exists(index_path):
            log(f"WARNING: aircraft database refresh failed ({e}); using stale cached index.")
            return load_index(index_path)
        raise AircraftDbError(
            f"Could not build aircraft type database and no cached copy exists: {e}"
        ) from e
