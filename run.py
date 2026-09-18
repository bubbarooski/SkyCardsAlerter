#!/usr/bin/env python3
"""Skycards Aircraft Alert Bot - one poll cycle per invocation (run via cron)."""
import sys
import time
from datetime import datetime

from src import aircraft_db, cities, config as config_mod, dedupe, geo, notify, opensky, wanted_list
from src.errors import SkyCardsError


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")


def log(msg):
    print(f"[{_timestamp()}] {msg}")


def _parse_city_flag(argv):
    """Returns the raw city key (no dash), '__help__', or None (use default)."""
    skip_next = False
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg in ("-h", "--help"):
            return "__help__"
        if arg == "--config":
            skip_next = True
            continue
        if arg.startswith("--"):
            continue
        if arg.startswith("-") and len(arg) > 1:
            return arg[1:]
    return None


def _get_config_path(argv):
    if "--config" in argv:
        idx = argv.index("--config")
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return "config.json"


def _print_help():
    print(__doc__)
    print("\nUsage: python3 run.py [-<cityFlag>] [--config path/to/config.json]\n")
    print("Available city flags:")
    for key, city in sorted(cities.CITIES.items()):
        print(f"  -{key:<15} {city['label']}")


def run(argv):
    city_flag = _parse_city_flag(argv)
    if city_flag == "__help__":
        _print_help()
        return 0

    try:
        cfg = config_mod.load_config(_get_config_path(argv))
    except SkyCardsError as e:
        log(f"WARNING: {e}")
        return 1

    try:
        city_key, city = cities.get_city(city_flag or cfg.get("default_city"))
    except SkyCardsError as e:
        log(f"WARNING: {e}")
        return 1

    radius_miles = cfg.get("radius_miles", 100)
    cooldown_hours = cfg.get("cooldown_hours", 2)

    log(f"Polling OpenSky (center: {city_key}, radius: {radius_miles}mi)...")

    bbox = geo.bounding_box(city["lat"], city["lon"], radius_miles)

    try:
        states = opensky.fetch_states(bbox, cfg)
    except SkyCardsError as e:
        log(f"WARNING: {e}")
        return 1

    try:
        wanted = wanted_list.load_wanted_list(cfg["wanted_list_path"])
    except SkyCardsError as e:
        log(f"WARNING: {e}")
        return 1

    try:
        aircraft_index = aircraft_db.ensure_index(cfg, log=log)
    except SkyCardsError as e:
        log(f"WARNING: {e}")
        return 1

    store = dedupe.load_store(cfg["dedupe_store_path"])
    now = time.time()

    in_range = []
    matches = []
    for state in states:
        distance = geo.haversine_miles(city["lat"], city["lon"], state["lat"], state["lon"])
        if distance > radius_miles:
            continue
        in_range.append(state)

        typecode = aircraft_index.get(state["icao24"])
        if not typecode or typecode not in wanted:
            continue
        matches.append((state, typecode, distance))

    log(f"{len(in_range)} aircraft in range, {len(matches)} matches")

    sent_count = 0
    for state, typecode, distance in matches:
        model_name = wanted.get(typecode, typecode)
        callsign = state["callsign"] or "unknown"
        icao24 = state["icao24"]

        if dedupe.is_on_cooldown(store, icao24, cooldown_hours, now):
            log(
                f"*** MATCH (on cooldown, no repeat alert): {model_name} ({typecode}) "
                f"- callsign {callsign} - {distance:.1f}mi away ***"
            )
            continue

        log(
            f"*** MATCH: {model_name} ({typecode}) - callsign {callsign} "
            f"- {distance:.1f}mi away ***"
        )

        click_url = notify.build_fr24_link(callsign if callsign != "unknown" else None)
        message = (
            f"{model_name} ({typecode}) spotted {distance:.1f}mi from {city['label']}. "
            f"Callsign: {callsign}."
        )
        sent = notify.send_ntfy(
            cfg.get("ntfy_topic"),
            title="Skycards: wanted aircraft nearby!",
            message=message,
            click_url=click_url,
            timeout=cfg.get("request_timeout_seconds", 20),
            log=log,
        )
        if sent:
            sent_count += 1
            dedupe.mark_alerted(store, icao24, now)

    dedupe.save_store(cfg["dedupe_store_path"], store)

    if sent_count:
        log(f"Sent {sent_count} notification(s).")

    return 0


def main():
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
