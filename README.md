# Dr. Suresh — weekly poster automation

Only the **date** changes each week. Everything else (name, times, locations,
phone, symptoms) is fixed and lives in `poster.html`. The generator computes the
upcoming Sunday, renders 4 posters, and emails them.

## Files
- `poster.html` — the design + all fixed text. **This is the only file you edit for content.**
- `generate.py` — renders the 4 posters and emails them.
- `backgrounds/` — your vetted, text-free background images (jpg/png). Rotates weekly.
- `output/` — generated PNGs land here.

## Test it in 30 seconds (no Python needed)
Double-click `poster.html` in a browser. To preview each location and a specific date:
```
poster.html?loc=0
poster.html?loc=1&today=2026-07-25
```
Confirm the Telugu renders correctly and the layout matches what you want. Adjust
the CSS font sizes / positions in `poster.html` until it looks right.

## Fill in the content
In `poster.html`, edit the `LOCATIONS` array:
- I could only extract **2** real locations from your sample posters. Fill in #2 and #3.
- Set each location's **fixed time string** once (marked `// TODO`).

## Backgrounds
Drop 10–15 approved, **text-free** health/ortho images into `backgrounds/`.
Rotation is deterministic by ISO week, so the same week always gets the same one.
To give each location its own background instead of one shared per week, change
`pick_background` to key off the location index too.

## Run the full pipeline
```
pip install playwright
playwright install chromium
export SMTP_USER="you@gmail.com"
export SMTP_PASS="your-gmail-app-password"   # NOT your login password
export MAIL_TO="brother@example.com"
python generate.py
```
If email creds are unset, it still renders to `output/` and just skips sending.

## Schedule (every Saturday 8am)
Linux/Mac cron:
```
0 8 * * 6  cd /path/to/poster && /usr/bin/python3 generate.py >> run.log 2>&1
```
Or run it on **GitHub Actions** (free, no server to babysit) with a
`schedule: cron` workflow that installs Playwright and runs `generate.py`.

## Gmail app password
Google Account → Security → 2-Step Verification → App passwords. Use that
16-char password as `SMTP_PASS`.

## WhatsApp (later, optional)
Skip for now. Emailing is enough — he forwards from his phone. If forwarding
becomes annoying, add WhatsApp Cloud API later; it needs a registered number and
approved template messages, which is real setup work for little gain here.

---
### Caveats (read these)
- **Untested render:** I built the code but couldn't run Chromium in my sandbox
  (no network). Do the browser preview above first; expect to nudge font sizes.
- **Telugu shaping is handled by the browser**, which is why this uses
  Playwright/Chromium and Google Fonts, not Pillow. Don't switch to Pillow.
- **AI is not in this pipeline.** Backgrounds are a hand-vetted pool. If you want
  fresh AI backgrounds, generate a batch, approve them by eye, then add to the pool.
