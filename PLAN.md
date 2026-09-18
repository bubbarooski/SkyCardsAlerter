# PLAN.md - design rationale

Full requirements are in `skycards-alert-bot-spec.md`. This file is the
"why" behind the implementation choices, for future reference.

## Layout
- `run.py` - single entry point, one poll cycle per process (matches the
  cron model: no daemon, no process supervision needed).
- `src/` - one module per concern (`cities`, `geo`, `config`, `opensky`,
  `aircraft_db`, `wanted_list`, `dedupe`, `notify`), each independently
  testable and each holding one responsibility.
- `data/` - runtime state and reference data, all gitignored except the
  `.example` files that show the shape.

## Key decisions
- **Bounding box + haversine, not just bounding box.** OpenSky's API only
  takes a lat/lon box, which is a square, not a circle. We ask OpenSky for a
  generous square around the city, then filter every candidate through
  `geo.haversine_miles` so the 100-mile cutoff is a true radius, not a
  square with 100mi "corners" that are actually ~140mi from center.
- **Aircraft type lookup goes through a derived index, not the raw CSV.**
  OpenSky's `aircraftDatabase.csv` metadata dump has ~30 columns and
  hundreds of thousands of rows. Re-parsing it in full on every 5-minute
  cron tick is wasteful. `aircraft_db.ensure_index()` builds a small
  `{icao24: typecode}` JSON index once per refresh window
  (`aircraft_db_max_age_days`, default 7) and every run just loads that.
  Still no database engine - it's a plain cache file, same spirit as the
  dedupe store.
- **OAuth2 client-credentials support, optional.** OpenSky's anonymous tier
  is rate-limited; polling every 5 minutes continuously benefits from a
  registered client. `opensky.py` fetches a bearer token when
  `opensky_client_id`/`opensky_client_secret` are set in config, and falls
  back to anonymous access when they're blank - no code changes needed
  either way. (OpenSky's auth flow has changed before and could again -
  worth a quick check against their current docs if this ever starts
  failing auth that used to work.)
- **Dedupe store keyed by ICAO24, not by (aircraft, poll).** A loitering or
  repeatedly-passing plane keeps the same ICAO24 hex across polls, so a
  simple `{icao24: last_alerted_unix_time}` file with a cooldown check is
  enough to prevent spam without any richer state.
- **Failures are warnings, not crashes.** Every expected failure mode
  (missing config, bad JSON, OpenSky down, rate-limited, ntfy down, no
  cached aircraft DB) raises a `SkyCardsError` subclass that `run.py` turns
  into one clear `WARNING:` line and a non-zero exit - never a raw
  traceback, per the "no silent failures, no raw stack traces" requirement.
  A cron job's stdout/stderr redirected to a log file stays legible this
  way.
- **Dedupe entries only get marked after a successful ntfy push.** If ntfy
  itself is unreachable, we deliberately don't mark the aircraft as
  "alerted" - the next poll cycle will retry the push instead of silently
  losing the alert.
