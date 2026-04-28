#!/usr/bin/env python3
"""Send the daily Bhagavad Gita shloka batch to a Telegram chat.

State (current chapter, verse, day count) is stored in a marker block at
the top of README.md so the script is fully stateless and works on
GitHub Actions: each run reads the position, sends the next batch, then
writes the advanced position back, which the workflow commits to git.
"""
from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("senddaily")

API_BASE = "https://vedicscriptures.github.io"
README_PATH = Path(__file__).parent / "README.md"

# Verse counts per chapter (1..18)
CHAPTERS = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28, 9: 34,
    10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78,
}
TOTAL_VERSES = sum(CHAPTERS.values())  # 700
DAILY_COUNT = 5

STATE_RE = re.compile(
    r"<!--\s*GITA_STATE\s*\n"
    r"chapter\s*=\s*(\d+)\s*\n"
    r"verse\s*=\s*(\d+)\s*\n"
    r"day\s*=\s*(\d+)\s*\n"
    r"-->",
    re.MULTILINE,
)


# ── Verse helpers ────────────────────────────────────────────────────

def absolute_verse_number(chapter: int, verse: int) -> int:
    return sum(CHAPTERS[c] for c in range(1, chapter)) + verse


def next_verse(chapter: int, verse: int) -> tuple[int, int]:
    if verse < CHAPTERS[chapter]:
        return chapter, verse + 1
    if chapter < 18:
        return chapter + 1, 1
    return 1, 1  # wrap around after 18:78


def batch_verses(chapter: int, verse: int, count: int = DAILY_COUNT):
    verses = [(chapter, verse)]
    ch, v = chapter, verse
    for _ in range(count - 1):
        ch, v = next_verse(ch, v)
        verses.append((ch, v))
    return verses


def fetch_verse(chapter: int, verse: int) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/slok/{chapter}/{verse}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error("Fetch %s:%s failed: %s", chapter, verse, e)
        return None


def format_message(chapter: int, verse: int, day: int) -> str | None:
    data = fetch_verse(chapter, verse)
    if not data:
        return None

    shloka = data.get("slok", "")
    hindi = next(
        (data[k]["ht"] for k in ("tej", "rams", "spiegel")
         if data.get(k, {}).get("ht")),
        None,
    )
    english = next(
        (data[k]["et"] for k in ("siva", "purohit", "prabhu", "gambir",
                                 "adi", "san", "raman", "abhinav")
         if data.get(k, {}).get("et")),
        None,
    )

    msg = (
        "🙏 *Shrimad Bhagavad Gita*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📖 *Chapter {chapter} | Verse {verse}*\n\n"
        f"📜 *Shloka:*\n{shloka}\n\n"
    )
    if hindi:
        msg += f"🇮🇳 *Hindi Translation:*\n{hindi}\n\n"
    if english:
        msg += f"🇬🇧 *English Translation:*\n{english}\n\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += f"📖 Verse {absolute_verse_number(chapter, verse)}/{TOTAL_VERSES} | Day {day}"
    return msg


# ── README state ─────────────────────────────────────────────────────

def read_state() -> tuple[int, int, int, str]:
    text = README_PATH.read_text(encoding="utf-8")
    m = STATE_RE.search(text)
    if not m:
        sys.exit("ERROR: GITA_STATE block not found in README.md")
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), text


def write_state(chapter: int, verse: int, day: int, original_text: str) -> None:
    new_block = (
        "<!-- GITA_STATE\n"
        f"chapter={chapter}\n"
        f"verse={verse}\n"
        f"day={day}\n"
        "-->"
    )
    README_PATH.write_text(
        STATE_RE.sub(new_block, original_text, count=1),
        encoding="utf-8",
    )


# ── Telegram ─────────────────────────────────────────────────────────

def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=15,
    )
    r.raise_for_status()


# ── Entrypoint ───────────────────────────────────────────────────────

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if not token or not chat_id:
        sys.exit("ERROR: TELEGRAM_BOT_TOKEN and CHAT_ID must be set (env or .env)")

    chapter, verse, day, original = read_state()
    log.info("Starting at Ch%s:%s (Day %s)", chapter, verse, day)

    verses = batch_verses(chapter, verse)
    sent = 0
    for ch, v in verses:
        msg = format_message(ch, v, day)
        if msg:
            send_telegram(token, chat_id, msg)
            sent += 1

    if sent == 0:
        sys.exit("ERROR: failed to send any verses; state not advanced.")

    last_ch, last_v = verses[-1]
    new_ch, new_v = next_verse(last_ch, last_v)
    write_state(new_ch, new_v, day + 1, original)
    log.info("Sent %s shlokas. Next: Ch%s:%s (Day %s)",
             sent, new_ch, new_v, day + 1)


if __name__ == "__main__":
    main()
