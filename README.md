# SkyCardsAlerter

Skycards Aircraft Alert Bot - polls [OpenSky Network](https://opensky-network.org/)
for live aircraft near a chosen city, matches against a "still need for
Skycards" wanted-aircraft list, and sends a free push notification via
[ntfy.sh](https://ntfy.sh/) when a needed plane is in range. Built to run
on a Raspberry Pi via cron, one poll cycle per invocation.

See `skycards-alert-bot-spec.md` for the full spec and `PLAN.md` for design
rationale.

## Quick start

```
pip install -r requirements.txt
cp config.example.json config.json                        # then fill in your ntfy topic
cp data/wanted_list.json.example data/wanted_list.json     # then fill in your aircraft
python3 run.py -jacksonvilleFL
```

Before this is actually useful, work through **`PRE_LAUNCH_CHECKLIST.md`**
- it covers the ntfy app setup, the aircraft database download, and cron.

## Usage

```
python3 run.py [-<cityFlag>] [--config path/to/config.json]
python3 run.py --help          # lists all available city flags
```

Defaults to Jacksonville, FL if no city flag is given. Add a new city by
adding an entry to `CITIES` in `src/cities.py` - no other code changes
needed.

## Tests

```
pip install -r requirements-dev.txt
python3 -m pytest -v
```

All network calls (OpenSky, ntfy) are mocked in tests - the suite runs
fully offline.

## Project layout

```
run.py                       entry point, one poll cycle per run
src/
  cities.py                  city flag -> lat/lon lookup table
  geo.py                     haversine distance + bounding box math
  config.py                  loads config.json with defaults
  opensky.py                 OpenSky API client (states + optional OAuth2)
  aircraft_db.py              icao24 -> type code lookup, cached from OpenSky's CSV
  wanted_list.py              loads the wanted-aircraft list
  dedupe.py                   cooldown/dedupe JSON store (read-modify-write)
  notify.py                   ntfy.sh push + Flightradar24 link builder
data/
  wanted_list.json.example    shape of the wanted list (real file is gitignored)
tests/                        pytest suite, network calls mocked
config.example.json           shape of the config (real file is gitignored)
PRE_LAUNCH_CHECKLIST.md       manual setup steps before running for real
PLAN.md                       design rationale
```

## Privacy

This repo is public. `config.json`, `data/wanted_list.json`,
`data/dedupe_store.json`, `data/aircraftDatabase.csv`, and
`data/aircraft_type_index.json` are all gitignored and must never be
committed - see `CLAUDE.md` for the full list of what stays local.
