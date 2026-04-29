# ICSE 2026 Result Checker — Autonomous Agent

An autonomous agent that runs on **GitHub's free infrastructure** (no laptop needed).
It checks `results.cisce.org` every 30 seconds starting at 10:45 AM IST on April 30, 2026, and sends you an instant **Telegram** notification when ICSE results go live.

---

## How It Works

```
GitHub Actions (free)  ──►  Polls results.cisce.org  ──►  Sends Telegram message
     at 10:45 AM IST            every 30 seconds           with your UID + links
```

- **No laptop required** — runs on GitHub's servers
- **No electricity worries** — GitHub handles 100% uptime
- **Instant notification** — Telegram message arrives in < 2 seconds
- **Logs saved** — you can view the full run history on GitHub

---

## Deploy in 5 Minutes (Tonight!)

### Step 1: Create Your Telegram Bot (2 min)

1. Open Telegram → Search `@BotFather` → Tap **Start**
2. Send: `/newbot`
3. Name it (e.g., "ICSE Result Bot")
4. Username must end in `bot` (e.g., `icse_2026_bot`)
5. **Copy the BOT TOKEN** shown (looks like `123456789:ABCdef...`)

Then get your Chat ID:
1. Search `@userinfobot` → Tap **Start**
2. Copy the number shown after **Id:**

### Step 2: Fork This Repo on GitHub (1 min)

1. Go to GitHub (github.com)
2. Create a **new repository** (name it anything, e.g., `icse-result-agent`)
3. Upload ALL files from this folder to that repo
   - `.github/workflows/icse-results.yml`
   - `src/check_results.py`

### Step 3: Add Your Secrets (2 min)

In your new GitHub repo:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these one by one:

| Secret Name | Value Example | Description |
|-------------|---------------|-------------|
| `TELEGRAM_BOT_TOKEN` | `123456789:ABCdefGHI...` | From BotFather |
| `TELEGRAM_CHAT_ID` | `123456789` | From @userinfobot |
| `UID` | `1786257` | Your 7-digit UID from admit card |
| `INDEX_NUMBER` | `123456` | Your index number from admit card |
| `COURSE_CODE` | `ICSE` | `ICSE` or `ISC` |

### Step 4: Test It NOW (30 sec)

1. In your GitHub repo, go to **Actions** tab
2. Click **ICSE Result Checker Agent**
3. Click **Run workflow** → **Run workflow**
4. Check Telegram — you should get a message in ~30 seconds!
   - It will say results are not live yet (which is correct — it's just a test)
   - This confirms your Telegram bot + secrets are working perfectly

### Step 5: Go to Sleep!

That's it. The agent is armed and will auto-trigger tomorrow at **10:45 AM IST** (15 min before 11 AM).

---

## What Happens Tomorrow

| Time (IST) | What the Agent Does |
|------------|---------------------|
| **10:45 AM** | GitHub Actions starts the agent |
| **10:45–11:00** | Checks every 30 sec (catching early release) |
| **11:00 AM** | Peak checking interval |
| **11:00+** | Continues until results are detected or 1.5 hours pass |
| **Results detected** | Instant Telegram message + GitHub logs saved |

---

## Viewing Your Agent Live

- **GitHub Actions tab**: Watch the agent run in real-time tomorrow
- **Logs**: Every check is printed — you'll see "indicators found: [...]" when results are close
- **Artifacts**: Full logs are saved automatically after each run

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No Telegram message on test | Make sure you sent `/start` to your bot first |
| "Secrets missing" error | Double-check all 5 secrets are added exactly as shown |
| Workflow not appearing | Make sure `.github/workflows/icse-results.yml` is in the right folder |
| Results not found | CISCE website might be overloaded — the SMS backup info is in your Telegram message |

---

## Files in This Package

| File | Purpose |
|------|---------|
| `.github/workflows/icse-results.yml` | The GitHub Actions workflow — the "agent brain" |
| `src/check_results.py` | The checker script that polls CISCE and sends Telegram |
| `index.html` | Optional status page you can open in browser for countdown |

---

## Why This Is Better Than Running on Your Laptop

| | Laptop Script | GitHub Agent |
|---|---|---|
| Laptop must stay on | Yes ❌ | No ✅ |
| Internet must stay on | Yes ❌ | No ✅ |
| Power failure kills it | Yes ❌ | No ✅ |
| Sleep mode kills it | Yes ❌ | No ✅ |
| Someone else can check | No ❌ | Yes — logs on GitHub ✅ |

---

Good luck tomorrow! 🎓🍀
