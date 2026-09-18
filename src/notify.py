"""Free push notifications via ntfy.sh, plus a Flightradar24 link builder."""
import requests


def build_fr24_link(callsign):
    if not callsign:
        return None
    slug = callsign.strip().replace(" ", "")
    if not slug:
        return None
    return f"https://www.flightradar24.com/{slug}"


def send_ntfy(topic, title, message, click_url=None, timeout=10, log=print):
    if not topic:
        log("WARNING: no ntfy_topic configured in config.json; skipping push notification.")
        return False

    url = f"https://ntfy.sh/{topic}"
    headers = {"Title": title}
    if click_url:
        headers["Click"] = click_url

    try:
        resp = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=timeout)
    except requests.RequestException as e:
        log(f"WARNING: ntfy push failed: {e}")
        return False

    if resp.status_code >= 300:
        log(f"WARNING: ntfy push failed (HTTP {resp.status_code}): {resp.text[:200]}")
        return False
    return True
