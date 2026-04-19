import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .services import format_verse_message, next_verse, random_verse, CHAPTERS
from .models import BotState

logger = logging.getLogger(__name__)


def get_or_create_state(chat_id):
    state, _ = BotState.objects.get_or_create(chat_id=str(chat_id))
    return state


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Handle incoming Telegram webhook updates."""
    try:
        data = json.loads(request.body)
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not chat_id or not text:
            return JsonResponse({"ok": True})

        if text == "/start":
            send_telegram_message(
                chat_id,
                "🙏 *नमस्ते!*\n\n"
                "मैं आपको प्रतिदिन श्रीमद्भगवद्गीता का एक श्लोक भेजूँगा।\n\n"
                "*Commands:*\n"
                "/today — आज का श्लोक\n"
                "/next — अगला श्लोक\n"
                "/random — कोई भी श्लोक\n"
                "/setshlok `chapter verse` — श्लोक सेट करें\n"
                "/status — वर्तमान स्थिति",
            )
        elif text == "/today":
            state = get_or_create_state(chat_id)
            msg = format_verse_message(state.current_chapter, state.current_verse, state.day_count)
            if msg:
                send_telegram_message(chat_id, msg)
            else:
                send_telegram_message(chat_id, "⚠️ श्लोक लोड करने में समस्या हुई। कृपया पुनः प्रयास करें।")
        elif text == "/next":
            state = get_or_create_state(chat_id)
            ch, v = next_verse(state.current_chapter, state.current_verse)
            state.current_chapter = ch
            state.current_verse = v
            state.day_count += 1
            state.save()
            msg = format_verse_message(ch, v, state.day_count)
            if msg:
                send_telegram_message(chat_id, msg)
        elif text == "/random":
            ch, v = random_verse()
            msg = format_verse_message(ch, v)
            if msg:
                send_telegram_message(chat_id, msg)
        elif text.startswith("/setshlok"):
            parts = text.split()
            if len(parts) == 3:
                try:
                    ch, v = int(parts[1]), int(parts[2])
                    if ch in CHAPTERS and 1 <= v <= CHAPTERS[ch]:
                        state = get_or_create_state(chat_id)
                        state.current_chapter = ch
                        state.current_verse = v
                        state.save()
                        send_telegram_message(chat_id, f"✅ अगला श्लोक सेट: अध्याय {ch}, श्लोक {v}")
                    else:
                        send_telegram_message(chat_id, "❌ गलत अध्याय/श्लोक। कृपया सही संख्या दें।")
                except ValueError:
                    send_telegram_message(chat_id, "❌ उपयोग: /setshlok 2 47")
            else:
                send_telegram_message(chat_id, "❌ उपयोग: /setshlok 2 47")
        elif text == "/status":
            state = get_or_create_state(chat_id)
            send_telegram_message(
                chat_id,
                f"📊 *स्थिति:*\n"
                f"अध्याय: {state.current_chapter}\n"
                f"श्लोक: {state.current_verse}\n"
                f"दिन: {state.day_count}\n"
                f"सक्रिय: {'हाँ ✅' if state.is_active else 'नहीं ❌'}",
            )

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return JsonResponse({"ok": True})


def send_telegram_message(chat_id, text):
    """Send a message via Telegram Bot API."""
    import requests

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")


@require_GET
def health_check(request):
    return JsonResponse({"status": "ok"})
