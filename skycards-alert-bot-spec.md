# Skycards Aircraft Alert Bot — Project Spec

## Build approach
This project is to be built "one-shot" — implemented, tested, and
self-verified as completely as possible without back-and-forth, then handed
off as a finished package. Since it can't be tested against the live
OpenSky/ntfy APIs or the actual Pi during that process, the build must
conclude with a **pre-launch checklist**: the specific things I still need
to manually check/verify/configure before setting this up and running it
for real (API accounts, secrets, live-data quirks, permissions, etc.).

## Overview
A small script that runs on a Raspberry Pi, checks for specific "wanted" aircraft
types near Jacksonville, FL (within 100 miles), and sends a free push
notification to my phone when one is nearby — so I can catch remaining
scarce/rare aircraft in the Skycards app.

## Goals
- Poll live flight data every 5 minutes.
- Filter to aircraft within 100 miles of a chosen center city, using true
  great-circle (haversine) distance, not just a bounding box.
- City is selectable via a command-line flag (e.g. `-jacksonvilleFL`,
  `-istanbulTUR`), not hardcoded, so I can point the bot at wherever I'm
  traveling.
- Match live aircraft types against a user-maintained "wanted list."
- Avoid duplicate/spammy alerts for the same aircraft.
- Send a free push notification to my phone with enough info to go find the plane.
- Run reliably, unattended, on a Raspberry Pi via cron.
- Runs entirely from a terminal, no GUI — easy to launch and check in on
  over SSH.
- Entire stack is free: Python, free data source, free notification channel,
  free to host on hardware I already own (the Pi).
- Code is going in a **public repo**, so nothing personally identifying goes
  into the committed source.

## Non-goals
- No GUI, no web dashboard, no database — dedupe store is a plain local JSON
  file, kept as simple as possible.
- No WhatsApp — using a free notification channel instead.
- Not trying to replicate Skycards' own catch mechanic — this is just a
  "heads up, go look" alert.

## Public repo / privacy
- Repo is public, so nothing personally identifying goes into committed code:
  - No home address, real name, or exact home coordinates in source. The
    default/example city in the lookup table can be a well-known public
    location (e.g. "Jacksonville, FL" is fine as a generic example city —
    it's not identifying on its own — but any home-specific fine-grained
    location should stay out).
  - My personal ntfy topic name is effectively a private "channel" — anyone
    who knows it can post to my phone or read what's sent. Treat it like a
    secret: not committed, loaded from a local config/env file instead.
  - My actual "wanted aircraft" list is personal but not sensitive/identifying
    — fine to keep local rather than committed either way, since it's just
    plane models.
  - No Pi hostnames, local network details, or file paths that reveal my
    machine/user setup.
- Practical approach: a `config.example.json` (or `.env.example`) gets
  committed showing the *shape* of config (empty/placeholder ntfy topic, a
  placeholder city), while the real `config.json`/`.env` with my actual
  topic and settings is gitignored and lives only on the Pi.

## City selection
- A small lookup table (JSON or a Python dict) mapping city flags to
  coordinates, e.g.:
  ```json
  {
    "jacksonvilleFL": { "lat": 30.3322, "lon": -81.6557 },
    "istanbulTUR": { "lat": 41.0082, "lon": 28.9784 }
  }
  ```
- Script accepts a flag like `-jacksonvilleFL` on the command line, looks up
  the coordinates, and uses that as the center point for the 100-mile radius.
- Default to Jacksonville, FL if no flag is given.
- Adding a new city is just adding an entry to the lookup table — no code
  changes needed.

## Data source: OpenSky Network (free tier)
- Endpoint: `/states/all` with a bounding box (`lamin`, `lomin`, `lamax`, `lomax`)
  covering roughly 100 miles around the selected city's coordinates.
- Returns live aircraft state vectors: ICAO24 hex, callsign, lat/lon, altitude,
  velocity, etc. — but **not** aircraft type directly.
- Aircraft type lookup: cross-reference each ICAO24 against OpenSky's free
  aircraft metadata database (downloadable CSV — `aircraftDatabase.csv`).
  Cache this file locally on the Pi and refresh it periodically (e.g. weekly),
  since it's large and doesn't change fast.
- Be mindful of OpenSky's free-tier rate limits (anonymous access is limited;
  consider registering a free OpenSky account for higher limits since we're
  polling every 5 min continuously).

## Wanted aircraft list
- A simple, user-editable list (JSON or CSV) of aircraft I still need for
  Skycards challenges.
- Skycards shows model names (e.g. "Boeing 787", "Airbus A380"); these need to
  be mapped to ICAO type codes (e.g. B788, A388) since that's what the OpenSky
  aircraft database uses.
- Format suggestion:
  ```json
  [
    { "model_name": "Boeing 787", "icao_type": "B788" },
    { "model_name": "Airbus A380", "icao_type": "A388" }
  ]
  ```
- I will supply the initial list of model names; the script (or a one-time
  helper) should map them to ICAO type codes.
- This list should be easy to update as I catch more aircraft and my "still
  need" list shrinks.

## Matching logic
1. Fetch live states within the bounding box.
2. For each aircraft, look up its ICAO type from the cached aircraft database
   using its ICAO24 hex.
3. Skip if type isn't in the wanted list.
4. Compute haversine distance from the selected city's coordinates; skip if
   > 100 miles.
5. Remaining aircraft are candidates for notification.

## Dedupe / cooldown
- Maintain a small local JSON file (no database) of
  `{ icao24: last_alerted_timestamp }`.
- Skip re-alerting for the same ICAO24 within a cooldown window (suggest 2
  hours, configurable) so a loitering or repeatedly-passing aircraft doesn't
  spam notifications.
- Script reads the file in, updates it in memory, and writes it back out —
  simple read-modify-write, no database engine involved.
- File should persist across script runs (it's a new process each cron run).

## Notification: ntfy.sh
- Free, no-account push notifications via HTTP POST to a topic URL
  (`https://ntfy.sh/<my-topic-name>`), delivered to the ntfy app on my phone.
- Message should include:
  - Aircraft model / type
  - Callsign (if available)
  - Distance from the selected city
  - A link to view the flight on Flightradar24
    (`https://www.flightradar24.com/<callsign>` or similar, if constructible)

## Phone setup (what I need to do, not code)
1. Install the **ntfy** app (iOS or Android) from the app store.
2. Pick a unique, hard-to-guess topic name (e.g. `shane-skycards-a1b2c3`) —
   this acts as the secret channel address.
3. In the app, subscribe to that topic name.
4. Put that same topic name in my local (gitignored) config on the Pi.
5. That's it — no account creation, no payment info, notifications just
   start arriving once the script posts to that topic.

## Terminal / CLI experience
- No GUI at all — everything happens through terminal output, so it's easy
  to run interactively or check on via SSH.
- On each poll cycle, print a concise status line, e.g.:
  - `[12:05:01] Polling OpenSky (center: jacksonvilleFL, radius: 100mi)...`
  - `[12:05:03] 214 aircraft in range, 0 matches`
- On a match, print a clearly distinguishable line (and still send the
  ntfy push), e.g.:
  - `[12:05:03] *** MATCH: Boeing 787 (B788) — callsign UAL123 — 42.1mi away ***`
- On errors (API failure, rate limit, etc.), print a clear warning line
  rather than a silent failure or stack trace dump, so it's obvious at a
  glance when checking in why nothing's come through.
- Runs fine as a one-off (`python3 script.py -jacksonvilleFL`) for manual
  checks, and identically under cron for scheduled runs — same script, same
  output style either way (cron output can be redirected to a log file).

## Deployment
- Runs on a Raspberry Pi.
- Triggered via cron every 5 minutes (not a long-running daemon — simpler,
  more crash-resistant, no process supervision needed).
- Config (city lookup table, radius, cooldown window, ntfy topic, paths to
  wanted-list and dedupe-store files) should live in a small config file or
  constants block, not hardcoded inline throughout the script.
- City flag is parsed from the command line at runtime (e.g. `python3
  script.py -istanbulTUR`).

## Open items / things to decide during implementation
- Whether to register a free OpenSky account for better rate limits.
- Exact cooldown window (defaulting to 2 hours unless changed).
- How to best construct a working Flightradar24 link per flight (callsign vs.
  flight number format may vary).
- Initial wanted list of model names (to be supplied) and their ICAO type
  code mapping.

## Acceptance criteria
- Script runs standalone via `python3 script.py` (defaults to Jacksonville,
  FL) and via `python3 script.py -<cityflag>` for any city in the lookup
  table, and again via cron with no manual steps.
- A test run with a known nearby wanted-type aircraft produces exactly one
  ntfy notification, not one per poll cycle.
- No notification for aircraft outside 100 miles or not on the wanted list.
- Aircraft database cache and dedupe JSON file survive script restarts.
