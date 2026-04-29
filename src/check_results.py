#!/usr/bin/env python3
"""
ICSE 2026 Result Checker — Autonomous Agent
============================================
Runs inside GitHub Actions. Polls results.cisce.org every 30 seconds.
Sends Telegram notification when results go live.

Environment variables (set via GitHub Secrets):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  UID, INDEX_NUMBER, COURSE_CODE
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# ── Config from GitHub Secrets ─────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
UID                = os.getenv("UID", "")
INDEX_NUMBER       = os.getenv("INDEX_NUMBER", "")
COURSE_CODE        = os.getenv("COURSE_CODE", "ICSE")

# ── Polling config ──────────────────────────────────────────────
RESULT_PORTAL_URL      = "https://results.cisce.org"
CISCE_HOME_URL         = "https://cisce.org"
CHECK_INTERVAL_SECONDS = 30
MAX_RETRIES            = 200  # ~1.6 hours of checking

# ── Telegram sender ─────────────────────────────────────────────
def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[SKIP] Telegram not configured via secrets.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        r = requests.post(url, json=payload, timeout=30)
        ok = r.status_code == 200 and r.json().get("ok")
        print(f"[TELEGRAM] {'SENT ✓' if ok else f'FAILED: {r.text}'}")
        return ok
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False

# ── Result portal check ───────────────────────────────────────────
def check_portal():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(RESULT_PORTAL_URL, headers=headers, timeout=15, allow_redirects=True)
        if r.status_code != 200:
            return {"status": f"HTTP {r.status_code}", "live": False, "url": r.url}

        soup = BeautifulSoup(r.text, "html.parser")
        page_text = soup.get_text().lower()

        indicators = [
            "result 2026", "year 2026", "examination result", "show result",
            "candidate uid", "index number", "marksheet", "result declaration",
            "icse 2026", "isc 2026",
        ]
        matches = [i for i in indicators if i in page_text]
        return {
            "status": "online",
            "live": len(matches) >= 2,
            "matches": matches,
            "url": r.url,
        }
    except requests.exceptions.ConnectionError:
        return {"status": "connection_error", "live": False, "url": RESULT_PORTAL_URL}
    except Exception as e:
        return {"status": f"exception: {e}", "live": False, "url": RESULT_PORTAL_URL}

# ── CISCE homepage check ─────────────────────────────────────────
def check_homepage():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(CISCE_HOME_URL, headers=headers, timeout=15)
        if r.status_code != 200:
            return {"status": f"HTTP {r.status_code}", "live": False}

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text().lower()

        links = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            t = a.get_text().lower()
            if "2026" in t and any(w in t for w in ["result", "examination", "mark"]):
                links.append({"text": a.get_text().strip(), "href": href})

        live = "2026" in text and any(w in text for w in ["result", "results", "declared"])
        return {"status": "online", "live": live, "links": links}
    except Exception as e:
        return {"status": f"exception: {e}", "live": False}

# ── Main loop ────────────────────────────────────────────────────
def main():
    print("=" * 66)
    print("   ICSE 2026 RESULT CHECKER — AUTONOMOUS AGENT RUNNING")
    print("=" * 66)
    print(f"   UID:         {UID or '(not set)'}")
    print(f"   Index:       {INDEX_NUMBER or '(not set)'}")
    print(f"   Course:      {COURSE_CODE}")
    print(f"   Telegram:    {'CONFIGURED ✓' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'NOT CONFIGURED'}")
    print(f"   IST Time:    {datetime.now().astimezone().__str__()}")
    print("=" * 66)
    print()

    # Validate config
    if not UID or not INDEX_NUMBER:
        print("[FATAL] UID and INDEX_NUMBER secrets are missing!")
        print("        Please add them in GitHub repo Settings → Secrets.")
        sys.exit(1)

    found = False
    attempt = 0

    while not found and attempt < MAX_RETRIES:
        attempt += 1
        now_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{now_str}] Attempt {attempt}/{MAX_RETRIES}")

        portal = check_portal()
        homepage = check_homepage()

        print(f"   Portal:     {portal['status']} | indicators: {portal.get('matches', [])}")
        print(f"   Homepage:   {homepage['status']} | links: {len(homepage.get('links', []))}")

        if portal["live"] or homepage["live"]:
            found = True
            print("\n" + "!" * 66)
            print("   RESULTS ARE LIVE!")
            print("!" * 66)

            msg = (
                f"🎓 *ICSE RESULTS 2026 ARE LIVE!* 🎓\n\n"
                f"Results declared on CISCE website.\n\n"
                f"🔗 [results.cisce.org](https://results.cisce.org)\n"
                f"🔗 [cisce.org](https://cisce.org)\n\n"
                f"📋 Your Credentials:\n"
                f"• UID: `{UID}`\n"
                f"• Index: `{INDEX_NUMBER}`\n"
                f"• Course: `{COURSE_CODE}`\n\n"
                f"📱 *SMS Alternative:*\n"
                f"Send: `{COURSE_CODE} {UID}` to `09248082883`\n\n"
                f"Best of luck! 🍀"
            )
            send_telegram(msg)
            print("\n   → Direct link: https://results.cisce.org")
            print(f"   → SMS: {COURSE_CODE} {UID} → 09248082883")
            break
        else:
            print(f"   [x] Not live. Retrying in {CHECK_INTERVAL_SECONDS}s...\n")
            time.sleep(CHECK_INTERVAL_SECONDS)

    if not found:
        print("\n[!] Max retries reached. Results may be delayed.")
        send_telegram(
            f"⚠️ ICSE Result Checker Alert\n\n"
            f"Been checking for 1.5+ hours but results may not be live yet.\n"
            f"Check manually: https://results.cisce.org\n"
            f"SMS: {COURSE_CODE} {UID} → 09248082883"
        )

if __name__ == "__main__":
    main()
