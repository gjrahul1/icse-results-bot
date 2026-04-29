#!/usr/bin/env python3
"""
ICSE 2026 Result Fetcher — Fully Agentic with Human-in-the-Loop
================================================================
This agent runs inside GitHub Actions, opens a real browser,
fills credentials, captures the CAPTCHA, sends it to Telegram,
waits for your reply, submits the form, and sends back your
FULL marksheet with every subject and mark.

Environment variables (GitHub Secrets):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  UID, INDEX_NUMBER, COURSE_CODE
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# ── Config from secrets ──────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
UID       = os.getenv("UID", "")
INDEX_NO  = os.getenv("INDEX_NUMBER", "")
COURSE    = os.getenv("COURSE_CODE", "ICSE")

# ── Telegram helpers ──────────────────────────────────────────────

def telegram_api(method, payload=None, files=None, timeout=30):
    if not BOT_TOKEN:
        return None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if files:
            r = requests.post(url, data=payload, files=files, timeout=timeout)
        else:
            r = requests.post(url, json=payload, timeout=timeout)
        return r.json()
    except Exception as e:
        print(f"[Telegram API Error] {method}: {e}")
        return None

def send_text(text):
    return telegram_api("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

def send_photo(photo_path, caption=""):
    payload = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        return telegram_api("sendPhoto", payload, files=files)

def poll_for_reply(max_wait_seconds=600, poll_interval=5):
    print(f"[AGENT] Polling Telegram for your CAPTCHA reply (max {max_wait_seconds}s)...")
    last_update_id = 0
    start_time = time.time()
    
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={"limit": 100},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("ok") and data.get("result"):
                last_update_id = max(u["update_id"] for u in data["result"])
    except Exception as e:
        print(f"[WARN] Could not fetch initial updates: {e}")
    
    while time.time() - start_time < max_wait_seconds:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": last_update_id + 1, "limit": 10},
                timeout=10
            )
            if r.status_code != 200:
                time.sleep(poll_interval)
                continue
            data = r.json()
            if not data.get("ok"):
                time.sleep(poll_interval)
                continue
            for update in data.get("result", []):
                last_update_id = max(last_update_id, update["update_id"])
                msg = update.get("message", {})
                if not msg:
                    continue
                if str(msg.get("chat", {}).get("id")) != str(CHAT_ID):
                    continue
                text = msg.get("text", "").strip()
                if text:
                    print(f"[AGENT] Received reply: '{text}'")
                    return text
        except Exception as e:
            print(f"[WARN] Poll error: {e}")
        elapsed = int(time.time() - start_time)
        remaining = max_wait_seconds - elapsed
        print(f"[AGENT] Waiting... {elapsed}s elapsed, {remaining}s left", end="\r")
        time.sleep(poll_interval)
    return None

# ── Browser automation ────────────────────────────────────────────

def run_browser_agent():
    print("=" * 66)
    print("   ICSE 2026 RESULT FETCHER — AGENTIC MODE")
    print("=" * 66)
    print(f"   UID:     {UID or '(not set)'}")
    print(f"   Index:   {INDEX_NO or '(not set)'}")
    print(f"   Course:  {COURSE}")
    print(f"   Telegram: {'CONFIGURED ✓' if BOT_TOKEN and CHAT_ID else 'NOT CONFIGURED'}")
    print("=" * 66)
    print()
    
    if not UID or not INDEX_NO:
        print("[FATAL] UID and INDEX_NUMBER secrets are missing!")
        sys.exit(1)
    
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        print("[FATAL] Playwright not installed.")
        sys.exit(1)
    
    print("[AGENT] Launching headless Chromium browser...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)
        page = context.new_page()
        
        try:
            # Step 1: Navigate
            print("[AGENT] Navigating to results.cisce.org...")
            page.goto("https://results.cisce.org", wait_until="networkidle", timeout=30000)
            page.screenshot(path="step1_portal_loaded.png")
            print("[AGENT] Portal loaded. Screenshot: step1_portal_loaded.png")
            
            # Step 1b: Check if results are live
            print("[AGENT] Checking if result form is available...")
            page_text = page.locator("body").inner_text().lower()
            if "will be published" in page_text or "results will be" in page_text:
                print("[AGENT] Results not declared yet. Page shows placeholder.")
                send_text(
                    "⏳ *ICSE Result Agent Update*\n\n"
                    "Portal loaded but results are **not declared yet**.\n"
                    "The page shows: \"results will be published on 30/04/2026 11:00 AM IST\"\n\n"
                    "Agent will retry in the next scheduled run."
                )
                sys.exit(0)
            
            send_text(
                f"🤖 *ICSE Result Agent Started*\n\n"
                f"Portal loaded successfully.\n"
                f"Filling your credentials now...\n\n"
                f"⏱ IST: `{datetime.now().astimezone().__str__()}`"
            )
            
            # Step 2: Fill Course
            print(f"[AGENT] Selecting course: {COURSE}")
            try:
                page.select_option("select", COURSE)
            except:
                try:
                    page.click(f"text={COURSE}")
                except:
                    try:
                        page.locator(f"[value='{COURSE}']").click()
                    except Exception as e:
                        print(f"[WARN] Could not auto-select course: {e}")
            
            # Step 3: Fill UID — using :visible to skip hidden inputs
            print(f"[AGENT] Filling UID: {UID}")
            try:
                uid_selectors = [
                    "input:visible[name*='uid' i]",
                    "input:visible[name*='UID' i]",
                    "input:visible[id*='uid' i]",
                    "input:visible[placeholder*='UID' i]",
                    "input:visible[placeholder*='Unique' i]",
                    "input:visible[name*='candidate' i]",
                    "input:visible[name*='code' i]",
                    "input[type='text']:visible",
                ]
                filled = False
                for sel in uid_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.fill(sel, UID)
                            print(f"[AGENT] UID filled using: {sel}")
                            filled = True
                            break
                    except Exception:
                        continue
                if not filled:
                    page.locator("input[type='text']:visible").first.fill(UID)
                    print("[AGENT] UID filled into first visible text input")
            except Exception as e:
                print(f"[ERROR] Could not fill UID: {e}")
                page.screenshot(path="error_uid.png")
                send_photo("error_uid.png", caption=f"❌ Failed to fill UID: {e}")
                sys.exit(1)
            
            # Step 4: Fill Index Number
            print(f"[AGENT] Filling Index Number: {INDEX_NO}")
            try:
                idx_selectors = [
                    "input:visible[name*='index' i]",
                    "input:visible[name*='INDEX' i]",
                    "input:visible[id*='index' i]",
                    "input:visible[placeholder*='index' i]",
                    "input:visible[placeholder*='Index' i]",
                    "input:visible[placeholder*='roll' i]",
                    "input:visible[name*='roll' i]",
                ]
                filled = False
                for sel in idx_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.fill(sel, INDEX_NO)
                            print(f"[AGENT] Index filled using: {sel}")
                            filled = True
                            break
                    except Exception:
                        continue
                if not filled:
                    inputs = page.locator("input[type='text']:visible").all()
                    if len(inputs) >= 2:
                        inputs[1].fill(INDEX_NO)
                        print("[AGENT] Index filled into second visible text input")
                    else:
                        raise Exception("Could not find a second visible text input for Index")
            except Exception as e:
                print(f"[ERROR] Could not fill Index: {e}")
                page.screenshot(path="error_index.png")
                send_photo("error_index.png", caption=f"❌ Failed to fill Index: {e}")
                sys.exit(1)
            
            page.screenshot(path="step2_form_filled.png")
            print("[AGENT] Form filled. Screenshot: step2_form_filled.png")
            
            # Step 5: Capture CAPTCHA
            print("[AGENT] Locating CAPTCHA...")
            captcha_found = False
            captcha_image_path = "captcha.png"
            
            try:
                img_selectors = [
                    "img[id*='captcha' i]",
                    "img[class*='captcha' i]",
                    "img[src*='captcha' i]",
                    "img[alt*='captcha' i]",
                    "img[src*='generate' i]",
                ]
                for sel in img_selectors:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).screenshot(path=captcha_image_path)
                        captcha_found = True
                        print(f"[AGENT] CAPTCHA captured using: {sel}")
                        break
            except Exception as e:
                print(f"[WARN] Image CAPTCHA capture failed: {e}")
            
            if not captcha_found:
                try:
                    captcha_input_selectors = [
                        "input:visible[name*='captcha' i]",
                        "input:visible[id*='captcha' i]",
                        "input:visible[class*='captcha' i]",
                        "input:visible[placeholder*='captcha' i]",
                        "input:visible[placeholder*='security' i]",
                        "input:visible[placeholder*='code' i]",
                        "input:visible[name*='security' i]",
                    ]
                    for sel in captcha_input_selectors:
                        if page.locator(sel).count() > 0:
                            box = page.locator(sel).bounding_box()
                            if box:
                                page.screenshot(
                                    path=captcha_image_path,
                                    clip={
                                        "x": max(0, box["x"] - 200),
                                        "y": max(0, box["y"] - 100),
                                        "width": box["width"] + 400,
                                        "height": box["height"] + 200,
                                    }
                                )
                                captcha_found = True
                                print(f"[AGENT] CAPTCHA region captured around: {sel}")
                                break
                except Exception as e:
                    print(f"[WARN] Region capture failed: {e}")
            
            if not captcha_found:
                print("[AGENT] Taking full-page screenshot for CAPTCHA...")
                page.screenshot(path=captcha_image_path)
                captcha_found = True
            
            # Step 6: Send CAPTCHA to Telegram
            if captcha_found and Path(captcha_image_path).exists():
                print("[AGENT] Sending CAPTCHA to your Telegram...")
                send_photo(
                    captcha_image_path,
                    caption=(
                        "🎓 *ICSE Result Agent needs your help!*\n\n"
                        "I've filled your credentials on the CISCE portal.\n"
                        "Please **reply with the CAPTCHA code** you see in this image.\n\n"
                        "⏱ You have *10 minutes* to reply.\n"
                        "Just send the numbers/letters — nothing else!"
                    )
                )
                send_text(
                    f"📋 *Your pre-filled details:*\n"
                    f"• UID: `{UID}`\n"
                    f"• Index: `{INDEX_NO}`\n"
                    f"• Course: `{COURSE}`\n\n"
                    f"Reply with the CAPTCHA only (e.g., `7x9k2p`)"
                )
            else:
                print("[ERROR] Could not capture CAPTCHA!")
                send_text("❌ Agent could not capture CAPTCHA. Please check manually: https://results.cisce.org")
                sys.exit(1)
            
            # Step 7: Wait for user's CAPTCHA reply
            print("[AGENT] Waiting for your CAPTCHA reply via Telegram...")
            captcha_text = poll_for_reply(max_wait_seconds=600, poll_interval=5)
            
            if not captcha_text:
                print("[AGENT] No reply received within 10 minutes. Aborting.")
                send_text("⏱ *Agent timed out waiting for your CAPTCHA reply.*\n\nYou can trigger the workflow again from GitHub Actions.")
                sys.exit(1)
            
            print(f"[AGENT] CAPTCHA received: '{captcha_text}'")
            send_text(f"✅ CAPTCHA received: `{captcha_text}`. Submitting form now...")
            
            # Step 8: Fill CAPTCHA and Submit
            try:
                captcha_input_selectors = [
                    "input:visible[name*='captcha' i]",
                    "input:visible[id*='captcha' i]",
                    "input:visible[class*='captcha' i]",
                    "input:visible[placeholder*='captcha' i]",
                    "input:visible[placeholder*='security' i]",
                    "input:visible[placeholder*='code' i]",
                    "input:visible[name*='security' i]",
                ]
                filled = False
                for sel in captcha_input_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.fill(sel, captcha_text)
                            print(f"[AGENT] CAPTCHA filled into: {sel}")
                            filled = True
                            break
                    except Exception:
                        continue
                if not filled:
                    inputs = page.locator("input[type='text']:visible").all()
                    for inp in inputs:
                        if not inp.input_value():
                            inp.fill(captcha_text)
                            print("[AGENT] CAPTCHA filled into last empty visible input")
                            filled = True
                            break
                if not filled:
                    raise Exception("Could not find empty input to fill CAPTCHA")
            except Exception as e:
                print(f"[ERROR] Could not fill CAPTCHA: {e}")
                page.screenshot(path="error_captcha_fill.png")
                send_photo("error_captcha_fill.png", caption=f"❌ Failed to enter CAPTCHA: {e}")
                sys.exit(1)
            
            page.screenshot(path="step3_before_submit.png")
            
            # Click submit
            print("[AGENT] Clicking 'Show Result'...")
            try:
                submit_selectors = [
                    "button:has-text('Show Result')",
                    "button:has-text('Submit')",
                    "button:has-text('Get Result')",
                    "button:has-text('View')",
                    "input[type='submit']",
                    "button[type='submit']",
                    "button:has-text('Result')",
                    "button:has-text('Go')",
                ]
                clicked = False
                for sel in submit_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.click(sel)
                            print(f"[AGENT] Clicked submit using: {sel}")
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    page.locator("input:visible").last.press("Enter")
                    print("[AGENT] Submitted by pressing Enter")
            except Exception as e:
                print(f"[ERROR] Could not submit form: {e}")
                send_text("❌ Agent could not submit the form. Please check manually.")
                sys.exit(1)
            
            # Step 9: Wait for result page
            print("[AGENT] Waiting for result page to load...")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(3)
            except PlaywrightTimeout:
                print("[WARN] Network idle timeout, proceeding anyway...")
            
            page.screenshot(path="step4_result_page.png")
            print("[AGENT] Result page loaded. Screenshot: step4_result_page.png")
            
            send_photo("step4_result_page.png", caption="📄 *Result page loaded!* Analyzing marksheet now...")
            
            # Step 10: Scrape marks
            print("[AGENT] Scraping marks from result page...")
            html = page.content()
            marks_data = []
            
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                tables = soup.find_all("table")
                for table in tables:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            text = [c.get_text(strip=True) for c in cells]
                            if any(keyword in " ".join(text).lower() for keyword in 
                                   ["english", "math", "science", "hindi", "social", "physics", 
                                    "chemistry", "biology", "computer", "marksheet", "mark", "grade", "percentage"]):
                                marks_data.append(" | ".join(text))
            except Exception as e:
                print(f"[WARN] Table parsing failed: {e}")
            
            page_text = page.locator("body").inner_text()
            result_message = "🎓 *ICSE RESULTS 2026 — YOUR MARKSHEET* 🎓\n\n"
            
            if marks_data:
                result_message += "📊 *Subject-wise Marks:*\n```\n"
                for line in marks_data[:20]:
                    result_message += line + "\n"
                result_message += "```\n\n"
            
            key_lines = []
            for line in page_text.split("\n"):
                line = line.strip()
                if line and len(line) > 2 and len(line) < 200:
                    if any(k in line.lower() for k in [
                        "name", "candidate", "school", "uid", "index", "mark", 
                        "grade", "percentage", "result", "pass", "fail",
                        "english", "math", "science", "hindi", "social", 
                        "physics", "chemistry", "biology", "computer", "history",
                        "geography", "economics", "commerce", "biology"
                    ]):
                        key_lines.append(line)
            
            if key_lines and not marks_data:
                result_message += "📋 *Extracted Details:*\n"
                for line in key_lines[:30]:
                    result_message += f"• {line}\n"
                result_message += "\n"
            
            result_message += (
                f"⏱ *Fetched at:* `{datetime.now().strftime('%d %b %Y, %I:%M %p IST')}`\n\n"
                f"📷 Full screenshot attached above.\n"
                f"🔗 https://results.cisce.org"
            )
            
            MAX_LEN = 4000
            if len(result_message) > MAX_LEN:
                chunks = [result_message[i:i+MAX_LEN] for i in range(0, len(result_message), MAX_LEN)]
                for i, chunk in enumerate(chunks):
                    send_text(f"📄 Part {i+1}/{len(chunks)}:\n{chunk}")
                    time.sleep(1)
            else:
                send_text(result_message)
            
            with open("result_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("[AGENT] Raw HTML saved: result_page.html")
            
            print("\n" + "=" * 66)
            print("   ✅ RESULT FETCHED AND SENT TO YOUR TELEGRAM!")
            print("=" * 66)
            
        except Exception as e:
            print(f"\n[FATAL ERROR] {type(e).__name__}: {e}")
            try:
                page.screenshot(path="error_fatal.png")
                send_photo("error_fatal.png", caption=f"❌ Agent crashed: {e}\n\nPlease check manually.")
            except:
                send_text(f"❌ Agent crashed: {e}\n\nPlease check manually: https://results.cisce.org")
            raise
        
        finally:
            context.close()
            browser.close()
            print("[AGENT] Browser closed.")

if __name__ == "__main__":
    run_browser_agent()
