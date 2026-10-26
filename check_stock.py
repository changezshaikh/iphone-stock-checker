#!/usr/bin/env python3
"""Check Apple AU same-day pickup stock for iPhone Duo and alert via WhatsApp (CallMeBot).

Environment variables:
  CALLMEBOT_PHONE   your WhatsApp number in international format, e.g. +61400000000
  CALLMEBOT_APIKEY  the API key CallMeBot sent you
  POSTCODE          optional, defaults to 3042
  STATE_FILE        optional, defaults to state.json
  DRY_RUN=1         print messages instead of sending them
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PARTS = {
    "MK2D4X/A": "iPhone Duo 256GB Star White",
    "MK2E4X/A": "iPhone Duo 256GB Night Sky",
    "MK2F4X/A": "iPhone Duo 512GB Star White",
    "MK2G4X/A": "iPhone Duo 512GB Night Sky",
}
POSTCODE = os.environ.get("POSTCODE", "3042")
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
# Warn once after this many failed checks in a row (12 x 5 min = 1 hour).
FAILURE_ALERT_THRESHOLD = 12

PRODUCT_URL = "https://www.apple.com/au/shop/buy-iphone/iphone-duo/7.6-inch-display-256gb-star-white"
# The older /shop/fulfillment-messages endpoint returns HTTP 541 everywhere; this one works.
STOCK_URL = "https://www.apple.com/au/shop/retail/pickup-message"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)


def fetch_stock():
    """Return {(part, store_name): available_bool}. Raises on any failure."""
    params = {"pl": "true", "location": POSTCODE}
    for i, part in enumerate(PARTS):
        params[f"parts.{i}"] = part
    req = urllib.request.Request(
        f"{STOCK_URL}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                 "Referer": PRODUCT_URL, "Accept-Language": "en-AU,en;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    stores = data["body"]["stores"]
    if not stores:
        raise ValueError("Apple returned no stores")
    result = {}
    for store in stores:
        name = store.get("storeName", store.get("storeNumber", "Unknown store"))
        for part, info in store.get("partsAvailability", {}).items():
            if part in PARTS:
                result[(part, name)] = info.get("pickupDisplay") == "available"
    return result


def send_whatsapp(text):
    if os.environ.get("DRY_RUN") == "1":
        print(f"[DRY RUN] WhatsApp: {text}")
        return
    phone = os.environ["CALLMEBOT_PHONE"]
    apikey = os.environ["CALLMEBOT_APIKEY"]
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
        {"phone": phone, "text": text, "apikey": apikey})
    with urllib.request.urlopen(url, timeout=30) as resp:
        print(f"WhatsApp sent (HTTP {resp.status})")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"available": [], "failures": 0, "failure_alerted": False}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    state = load_state()

    try:
        stock = fetch_stock()
    except Exception as e:  # network error, block page, changed JSON shape...
        detail = f"HTTP {e.code}" if isinstance(e, urllib.error.HTTPError) else repr(e)
        state["failures"] += 1
        print(f"Stock check failed ({state['failures']} in a row): {detail}")
        if state["failures"] >= FAILURE_ALERT_THRESHOLD and not state["failure_alerted"]:
            send_whatsapp(f"iPhone stock checker: Apple's stock check has failed "
                          f"{state['failures']} times in a row ({detail}). "
                          f"Alerts may not work until it recovers.")
            state["failure_alerted"] = True
        save_state(state)
        return 0

    if state["failure_alerted"]:
        send_whatsapp("iPhone stock checker: Apple's stock check is working again.")
    state["failures"] = 0
    state["failure_alerted"] = False

    now_available = sorted(f"{part}|{store}" for (part, store), ok in stock.items() if ok)
    newly = [k for k in now_available if k not in state["available"]]
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} checked {len(stock)} part/store pairs, "
          f"{len(now_available)} available, {len(newly)} new")

    if newly:
        lines = [f"- {PARTS[k.split('|')[0]]} at {k.split('|')[1]}" for k in newly]
        send_whatsapp("iPhone Duo available for pickup today!\n" + "\n".join(lines)
                      + f"\n{PRODUCT_URL}")

    state["available"] = now_available
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
