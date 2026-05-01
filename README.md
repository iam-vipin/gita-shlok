# 🙏 Gita Daily Bot

A tiny Python script that posts a batch of 5 shlokas from the Shrimad Bhagavad Gita — Sanskrit, Hindi, and English — to a Telegram chat once a day. Hosted for free on GitHub Actions. No server, no database.

<!-- GITA_STATE
chapter=1
verse=26
day=6
-->

## How it works

- A scheduled [GitHub Actions workflow](.github/workflows/daily.yml) runs [`senddaily.py`](senddaily.py) once a day.
- The script fetches the next 5 verses from the [Vedic Scriptures API](https://vedicscriptures.github.io/) and posts each to your Telegram chat.
- The current position (chapter / verse / day) lives in the `GITA_STATE` block at the top of this README. After every run, the workflow commits the advanced position back, so the next run picks up exactly where this one left off.
- After Chapter 18 finishes (verse 18:78), the bot wraps back to 1:1 and starts the cycle again.

## Setup

1. **Create a Telegram bot.** Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token it gives you.
2. **Get your chat id.** Message [@userinfobot](https://t.me/userinfobot) → `/start` → copy the id it replies with.
3. **Fork or clone this repo** and push it to your GitHub account.
4. **Add two repo secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `TELEGRAM_BOT_TOKEN`
   - `CHAT_ID`
5. **Allow Actions to commit back.** Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save. Without this the workflow can't push the updated state.
6. **Trigger it once manually** from the Actions tab (run the *Daily Gita Shloka* workflow) to confirm everything works. After that it runs automatically every day.

## Schedule

The workflow runs at `01:30 UTC` (= `07:00 IST`) daily. To change it, edit the `cron` line in [`.github/workflows/daily.yml`](.github/workflows/daily.yml). Cron is in UTC; subtract 5h30m to get IST. Test expressions at [crontab.guru](https://crontab.guru/).

> Note: GitHub's scheduled runs are best-effort and may be delayed 5–15 minutes (occasionally more) under load. That's normal.

## Reset or jump to a specific verse

Edit the `GITA_STATE` block at the top of this README and commit:

```html
<!-- GITA_STATE
chapter=2
verse=47
day=1
-->
```

The next run will start from the values you set.

## Run locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in TELEGRAM_BOT_TOKEN and CHAT_ID
python senddaily.py
```

This will send the next batch and update the README state, just like the workflow does.

## Credits

Verse content via the [Vedic Scriptures API](https://vedicscriptures.github.io/).
