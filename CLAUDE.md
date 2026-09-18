# CLAUDE.md

Standing context for Claude Code when working in this repo. Full design
rationale lives in `PLAN.md` — read that first for the "why."

## What this is
Skycards Aircraft Alert Bot — polls OpenSky for live aircraft near a chosen
city, matches against a wanted-aircraft list, sends free push notifications
via ntfy.sh when a needed plane is in range.

## Build approach
- Build this **one-shot**: implement, write tests, run tests, iterate until
  green, with minimal back-and-forth.
- Must end with a **pre-launch checklist** — a concrete list of things that
  need manual checking/setup before this actually runs for real (accounts,
  secrets, downloading reference data, cron setup, etc.). Don't skip this.

## Stack & constraints
- Python 3, stdlib + `requests` only unless there's a strong reason for more.
- No GUI — terminal output only. Print clear status lines each poll, a
  clearly distinguishable line on a match, and clear warnings on errors
  (no silent failures, no raw stack traces to the user).
- No database — dedupe/cooldown state is a plain local JSON file
  (read-modify-write), nothing heavier.
- Runs on a Raspberry Pi via cron — one poll cycle per invocation, not a
  long-running daemon.
- Entire stack must be free: free data source, free notification channel,
  no paid accounts required.
- City is not hardcoded — selected via a command-line flag
  (e.g. `-jacksonvilleFL`, `-istanbulTUR`) against a lookup table.

## Commands
- Run once: `python3 run.py -<cityFlag>` (e.g. `python3 run.py -jacksonvilleFL`)
- Run tests: `python3 -m pytest -v`
- Install: `pip install -r requirements.txt` (`requirements-dev.txt` adds
  pytest)

## Privacy — this repo is public
Never commit:
- The real `config.json` — contains the ntfy topic, which functions as a
  secret (anyone who knows it can push to or read the channel).
- `data/wanted_list.json` — actual Skycards progress.
- `data/dedupe_store.json` — runtime state.
- `data/aircraftDatabase.csv` — large downloaded reference data.

Only the `.example` versions of config/data files are committed. No real
coordinates, hostnames, file paths, or other personally-identifying details
belong in source — city data stays in the generic lookup table in
`src/cities.py`.
