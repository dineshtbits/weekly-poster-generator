#!/usr/bin/env python3
"""
Weekly poster generator for Dr. Suresh.

What it does:
  1. Picks the week's background from a rotating pool (deterministic).
  2. Renders 4 posters (one per location) from poster.html using headless Chromium.
  3. Emails all 4 PNGs to the doctor.

Only the date changes week to week; everything else lives in poster.html.

Setup (one time):
    pip install playwright
    playwright install chromium

Run:
    python generate.py
Schedule it every Saturday (see README).
"""

import os
import glob
import smtplib
import datetime as dt
from email.message import EmailMessage
from pathlib import Path
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
POSTER_HTML = HERE / "poster.html"
BG_DIR = HERE / "backgrounds"          # drop vetted .jpg/.png files here
THEMES_DIR = HERE / "themes"           # themes/<name>/*.jpg|png
ACTIVE_THEME = os.environ.get("THEME", "")          # override with THEME=blue; empty = auto-rotate
OUT_DIR = HERE / "output"
N_LOCATIONS = 3

# Email (use an app password, never your real one). Set via env vars.
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")            # your sending gmail
SMTP_PASS = os.environ.get("SMTP_PASS", "")            # gmail app password
MAIL_TO   = os.environ.get("MAIL_TO", "brother@example.com")


def upcoming_sunday(today: dt.date) -> dt.date:
    days_until = (6 - today.weekday()) % 7   # Mon=0..Sun=6; 0 if today is Sunday
    return today + dt.timedelta(days=days_until)


def pick_background(sunday: dt.date):
    """Deterministic weekly rotation through the pool. Same week -> same bg."""
    pool = sorted(glob.glob(str(BG_DIR / "*.jpg")) +
                  glob.glob(str(BG_DIR / "*.jpeg")) +
                  glob.glob(str(BG_DIR / "*.png")))
    if not pool:
        return None  # poster.html falls back to its gradient
    week_index = sunday.isocalendar()[1]         # ISO week number
    return pool[week_index % len(pool)]


def available_themes() -> list:
    """All theme folders that exist on disk, sorted alphabetically."""
    return sorted(d.name for d in THEMES_DIR.iterdir() if d.is_dir())


def pick_theme(sunday: dt.date) -> str:
    """Deterministic weekly theme rotation, or use THEME env var override."""
    if ACTIVE_THEME:
        return ACTIVE_THEME
    themes = available_themes()
    if not themes:
        raise RuntimeError(f"No theme folders found in {THEMES_DIR}")
    week_index = sunday.isocalendar()[1]
    return themes[week_index % len(themes)]


def pick_theme_image(sunday: dt.date, theme: str):
    """Deterministic weekly rotation through the chosen theme's images."""
    theme_dir = THEMES_DIR / theme
    pool = sorted(glob.glob(str(theme_dir / "*.jpg")) +
                  glob.glob(str(theme_dir / "*.jpeg")) +
                  glob.glob(str(theme_dir / "*.png")))
    if not pool:
        return None  # poster.html falls back to the SVG icon
    week_index = sunday.isocalendar()[1]
    return pool[week_index % len(pool)]


def render_posters(sunday: dt.date, bg_path, img_path, theme: str):
    OUT_DIR.mkdir(exist_ok=True)
    date_str = sunday.strftime("%d-%m-%Y")
    files = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350},
                                device_scale_factor=2)  # crisp export
        for i in range(N_LOCATIONS):
            params = f"?loc={i}&theme={theme}"
            if bg_path:
                params += f"&bg=backgrounds/{Path(bg_path).name}"
            if img_path:
                params += f"&img=themes/{theme}/{Path(img_path).name}"
            url = POSTER_HTML.as_uri() + params
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(600)  # let webfont settle
            out = OUT_DIR / f"poster_loc{i}_{date_str}.png"
            page.locator("#poster").screenshot(path=str(out))
            files.append(out)
            print("rendered", out.name)
        browser.close()
    return files


def send_email(files, sunday: dt.date):
    if not (SMTP_USER and SMTP_PASS):
        print("!! Email creds not set; skipping send. Files are in ./output")
        return
    msg = EmailMessage()
    msg["Subject"] = f"Sunday posters — {sunday.strftime('%d-%m-%Y')}"
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg.set_content("Attached: 3 posters for this Sunday. Forward each to its group.")
    for f in files:
        data = Path(f).read_bytes()
        msg.add_attachment(data, maintype="image", subtype="png", filename=Path(f).name)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    print("emailed", len(files), "posters to", MAIL_TO)


def main():
    sunday = upcoming_sunday(dt.date.today())
    theme = pick_theme(sunday)
    bg = pick_background(sunday)
    img = pick_theme_image(sunday, theme)
    print(f"upcoming Sunday: {sunday} | theme: {theme} ({len(available_themes())} themes) | image: {Path(img).name if img else '(SVG fallback)'}")
    files = render_posters(sunday, bg, img, theme)
    send_email(files, sunday)


if __name__ == "__main__":
    main()
