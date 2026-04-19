import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from bot.models import BotState, VerseHistory
from bot.services import format_verse_message, next_verse, get_batch_verses

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send daily Gita shloka to all active subscribers"

    def handle(self, *args, **options):
        states = BotState.objects.filter(is_active=True)

        if not states.exists():
            # If no subscribers yet, send to CHAT_ID from env
            chat_id = settings.CHAT_ID
            if chat_id:
                state, _ = BotState.objects.get_or_create(chat_id=chat_id)
                states = [state]
            else:
                self.stdout.write(self.style.WARNING("No active subscribers found."))
                return

        for state in states:
            verses = get_batch_verses(state.current_chapter, state.current_verse)
            sent = 0
            for ch, v in verses:
                msg = format_verse_message(ch, v, state.day_count)
                if msg:
                    self._send_message(state.chat_id, msg)
                    VerseHistory.objects.create(chat_id=state.chat_id, chapter=ch, verse=v)
                    sent += 1

            if sent > 0:
                last_ch, last_v = verses[-1]
                new_ch, new_v = next_verse(last_ch, last_v)
                state.current_chapter = new_ch
                state.current_verse = new_v
                state.day_count += 1
                state.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Sent {sent} shlokas to {state.chat_id}")
                )
            else:
                self.stdout.write(self.style.ERROR(f"Failed to fetch verses for {state.chat_id}"))

    @staticmethod
    def _send_message(chat_id, text):
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")
