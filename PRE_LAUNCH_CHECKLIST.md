# Pre-launch checklist

Things to do by hand before this runs for real - none of this can be
verified from inside the build since it depends on live accounts, live
APIs, and your actual Pi.

1. **Install deps.** On the Pi: `pip install -r requirements.txt` (or
   `requirements-dev.txt` if you also want to run the tests there).
2. **Create your real config.** Copy `config.example.json` -> `config.json`
   and fill in:
   - `ntfy_topic`: a unique, hard-to-guess string you invent (e.g.
     `shane-skycards-a1b2c3`). This is your private channel address -
     treat it like a password.
   - Review `radius_miles`, `cooldown_hours`, `default_city` (all have
     sane defaults already: 100mi / 2h / Jacksonville, FL).
3. **Create your real wanted list.** Copy
   `data/wanted_list.json.example` -> `data/wanted_list.json` and fill in
   the aircraft you still need for Skycards, as `{model_name, icao_type}`
   pairs. Skycards shows model names, not ICAO type codes - if you're
   unsure how to map a model name to its ICAO type code (e.g. "Boeing 787"
   -> which dash variant/code), send me the list of model names and I can
   help map them.
4. **Set up ntfy on your phone.**
   - Install the **ntfy** app (iOS or Android).
   - Subscribe to the exact same topic name you put in `config.json`.
   - No account or payment info needed.
5. **(Optional, recommended) Register a free OpenSky account.** Anonymous
   API access is rate-limited; polling every 5 minutes continuously is
   friendlier with a registered client. Create an API client at
   opensky-network.org and put the `client_id`/`client_secret` in
   `config.json`. Leave both blank to use anonymous access instead - the
   script works either way.
6. **Verify the aircraft database download still works.** First run will
   try to download `aircraftDatabase.csv` from the URL in config
   (`aircraft_db_url`). OpenSky occasionally reorganizes their dataset
   URLs - if the automatic download fails, grab the current metadata CSV
   from opensky-network.org's datasets page by hand and place it at
   `data/aircraftDatabase.csv`, then re-run.
7. **Do a manual test run before wiring up cron:**
   ```
   python3 run.py -jacksonvilleFL
   ```
   (or whatever city flag you'll actually use) and confirm it prints
   status lines with no `WARNING:` lines.
8. **Set up cron**, e.g. (adjust the path):
   ```
   */5 * * * * cd /home/pi/SkyCardsAlerter && /usr/bin/python3 run.py -jacksonvilleFL >> logs/skycards.log 2>&1
   ```
   Create the `logs/` directory first. This log will grow forever - keep
   an eye on it or add logrotate if it matters to you.
9. **Check outbound network access from the Pi** to
   `opensky-network.org`, `auth.opensky-network.org` (only needed if using
   OAuth), and `ntfy.sh`.
10. **Before pushing to the public repo**, confirm `git status` shows
    `config.json`, `data/wanted_list.json`, `data/dedupe_store.json`,
    `data/aircraftDatabase.csv`, and `data/aircraft_type_index.json` as
    untracked/ignored - none of them should ever be committed.

One more thing worth knowing: OpenSky's exact API/auth details could have
shifted since this was built - if requests start failing with auth errors
that used to work, it's worth a quick check against OpenSky's current docs
rather than assuming the code is wrong.
