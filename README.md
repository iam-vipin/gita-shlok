# 🙏 Gita Daily Bot — Django + Telegram

A Django-powered Telegram bot that sends you one shloka from Shrimad Bhagavad Gita daily with Hindi & English translations.

## Features
- 📖 Daily shloka delivery at 7 AM IST
- 🇮🇳 Hindi + 🇬🇧 English translations
- 📜 Original Sanskrit shloka
- 🎲 Random verse command
- 📊 Admin panel to manage subscribers
- 🔄 Auto-advances through all 700 verses

## Setup

### 1. Create Telegram Bot
- Open Telegram, search for @BotFather
- Send `/newbot`, follow prompts
- Copy the bot token

### 2. Get Your Chat ID
- Search for @userinfobot on Telegram
- Send `/start` — it will reply with your chat ID

### 3. Local Development
```bash
git clone <repo-url>
cd gita
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your bot token and chat ID
python manage.py migrate
python manage.py createsuperuser
python manage.py runbot  # Starts polling mode
```

### 4. Daily Scheduling (Local)
```bash
# Add to crontab (runs at 7 AM IST daily)
0 7 * * * cd /path/to/gita && /path/to/venv/bin/python manage.py senddaily
```

## Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/today` | Current shloka |
| `/next` | Next shloka |
| `/random` | Random shloka |
| `/setshlok 2 47` | Set specific verse |
| `/status` | Current progress |

## 🚀 Hosting Options (Best → Good)

### 1. Railway.app (⭐ Recommended)
- Free tier available, easiest Django hosting
- Push to GitHub → connect to Railway → auto deploys
- Add env vars in dashboard, add cron job for `senddaily`
- Cost: Free tier or ~$5/month

### 2. Render.com
- Free tier with auto-deploy from GitHub
- Add cron job via Render dashboard
- Cost: Free tier or ~$7/month

### 3. VPS (DigitalOcean/Hetzner)
- Full control, run bot in polling mode with systemd
- Use cron for daily scheduling
- Cost: ~$4-6/month

### 4. PythonAnywhere
- Free tier supports Django + scheduled tasks
- Perfect for this use case
- Cost: Free!

## API
Uses the free [Bhagavad Gita API](https://bhagavadgita.theaum.org/) by TheAum.org
# gita-shlok
