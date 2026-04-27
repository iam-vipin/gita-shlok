"""Send daily Gita shloka using README.md as state storage (no DB).

Designed for stateless schedulers like GitHub Actions. State is stored
between two HTML-comment markers in README.md so it can be committed back
to the repo after each run.
"""
import logging
import re
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bot.services import format_verse_message, get_batch_verses, next_verse

logger = logging.getLogger(__name__)

README_PATH = Path(settings.BASE_DIR) / "README.md"

STATE_RE = re.compile(
    r"<!--\s*GITA_STATE\s*\n"
    r"chapter\s*=\s*(\d+)\s*\n"
    r"verse\s*=\s*(\d+)\s*\n"
    r"day\s*=\s*(\d+)\s*\n"
    r"-->",
    re.MULTILINE,
)


def read_state():
    text = README_PATH.read_text(encoding="utf-8")
    m = STATE_RE.search(text)
    if not m:
        raise CommandError(
            "GITA_STATE block not found in README.md. "
            "Add the marker block (see README setup) before running."
        )
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), text


def write_state(chapter, verse, day, text):
    new_block = (
        "<!-- GITA_STATE\n"
        f"chapter={chapter}\n"
        f"verse={verse}\n"
        f"day={day}\n"
        "-->"
    )
    new_text = STATE_RE.sub(new_block, text, count=1)
    README_PATH.write_text(new_text, encoding="utf-8")


class Command(BaseCommand):
    help = "Send daily Gita shloka using README.md state (no DB required)."

    def handle(self, *args, **options):
        chat_id = settings.CHAT_ID
        if not chat_id:
            raise CommandError("CHAT_ID is not set in environment.")
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set in environment.")

        chapter, verse, day, text = read_state()
        self.stdout.write(f"Starting at Ch{chapter}:{verse} (Day {day})")

        verses = get_batch_verses(chapter, verse)
        sent = 0
        for ch, v in verses:
            msg = format_verse_message(ch, v, day)
            if msg:
                self._send_message(chat_id, msg)
                sent += 1

        if sent == 0:
            raise CommandError("Failed to fetch any verses; state not advanced.")

        last_ch, last_v = verses[-1]
        new_ch, new_v = next_verse(last_ch, last_v)
        write_state(new_ch, new_v, day + 1, text)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent {sent} shlokas to {chat_id}. "
                f"Next: Ch{new_ch}:{new_v} (Day {day + 1})"
            )
        )

    @staticmethod
    def _send_message(chat_id, text):
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")
            raise
