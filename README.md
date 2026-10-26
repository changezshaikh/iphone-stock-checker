# iPhone Duo stock checker

Checks Apple AU same-day pickup stock near postcode 3042 every 5 minutes (via GitHub Actions)
and sends a WhatsApp message when any of these become available:

| Part     | Model                     |
|----------|---------------------------|
| MK2D4X/A | 256GB Star White          |
| MK2E4X/A | 256GB Night Sky           |
| MK2F4X/A | 512GB Star White          |
| MK2G4X/A | 512GB Night Sky           |

You get one message per model/store when it comes into stock (not every 5 minutes), plus a
warning if Apple's stock check keeps failing for an hour.

## Setup

1. **Get a CallMeBot WhatsApp key**
   - Save `+34 644 66 32 62` in your phone contacts (check https://www.callmebot.com/blog/free-api-whatsapp-messages/ for the current number).
   - Send it the WhatsApp message: `I allow callmebot to send me messages`
   - It replies with your API key.

2. **Create a private GitHub repo** and push this folder to it.

3. **Add secrets** in the repo: Settings → Secrets and variables → Actions → New repository secret
   - `CALLMEBOT_PHONE`: your number, e.g. `+61400000000`
   - `CALLMEBOT_APIKEY`: the key from step 1

4. **Test it**: Actions tab → "Check iPhone stock" → Run workflow. Check the log.

The schedule starts automatically after that. To stop it, disable the workflow in the Actions tab.

## Run locally

```bash
DRY_RUN=1 python3 check_stock.py
```

## Notes

- GitHub's 5-minute schedule is best-effort; runs are often a few minutes late.
- GitHub disables scheduled workflows in repos with no activity for 60 days.
- Apple may block requests from GitHub's servers. If you get the "has failed 12 times" warning,
  that's likely why, and running it from your own Mac is the fallback.
