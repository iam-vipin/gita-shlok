import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest

from bot.models import BotState, VerseHistory
from bot.services import format_verse_message, next_verse, random_verse, get_batch_verses, CHAPTERS, DAILY_COUNT

logger = logging.getLogger(__name__)


@sync_to_async
def get_or_create_state(chat_id):
    state, _ = BotState.objects.get_or_create(chat_id=str(chat_id))
    return state


@sync_to_async
def save_state(state):
    state.save()


@sync_to_async
def create_history(chat_id, chapter, verse):
    VerseHistory.objects.create(chat_id=chat_id, chapter=chapter, verse=verse)


class Command(BaseCommand):
    help = "Run the Telegram bot in polling mode"

    def handle(self, *args, **options):
        self.stdout.write("Starting Gita Bot in polling mode...")

        request = HTTPXRequest(connect_timeout=20.0, read_timeout=20.0)
        app = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .request(request)
            .build()
        )

        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("today", today_cmd))
        app.add_handler(CommandHandler("next", next_cmd))
        app.add_handler(CommandHandler("random", random_cmd))
        app.add_handler(CommandHandler("setshlok", setshlok_cmd))
        app.add_handler(CommandHandler("status", status_cmd))

        self.stdout.write(self.style.SUCCESS("Bot is running! Press Ctrl+C to stop."))
        app.run_polling(drop_pending_updates=True)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await get_or_create_state(chat_id)
    await update.message.reply_text(
        "🙏 *Namaste!*\n\n"
        f"I will send you {DAILY_COUNT} shlokas from Shrimad Bhagavad Gita daily.\n\n"
        "*Commands:*\n"
        f"/today — Today's {DAILY_COUNT} shlokas\n"
        f"/next — Next {DAILY_COUNT} shlokas\n"
        "/random — Random shloka\n"
        "/setshlok `chapter verse` — Set starting verse\n"
        "/status — Current progress",
        parse_mode="Markdown",
    )


async def send_batch(update, state, advance=False):
    """Send a batch of shlokas."""
    verses = get_batch_verses(state.current_chapter, state.current_verse)
    sent = 0
    for i, (ch, v) in enumerate(verses):
        msg = format_verse_message(ch, v, state.day_count)
        if msg:
            await update.message.reply_text(msg, parse_mode="Markdown")
            sent += 1

    if advance and sent > 0:
        last_ch, last_v = verses[-1]
        new_ch, new_v = next_verse(last_ch, last_v)
        for ch, v in verses:
            await create_history(str(update.effective_chat.id), ch, v)
        state.current_chapter = new_ch
        state.current_verse = new_v
        state.day_count += 1
        await save_state(state)

    if sent == 0:
        await update.message.reply_text("⚠️ Failed to load shlokas. Please try again.")


async def today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    state = await get_or_create_state(chat_id)
    await send_batch(update, state, advance=False)


async def next_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    state = await get_or_create_state(chat_id)
    await send_batch(update, state, advance=True)


async def random_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ch, v = random_verse()
    msg = format_verse_message(ch, v)
    if msg:
        await update.message.reply_text(msg, parse_mode="Markdown")


async def setshlok_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    args = context.args
    if len(args) == 2:
        try:
            ch, v = int(args[0]), int(args[1])
            if ch in CHAPTERS and 1 <= v <= CHAPTERS[ch]:
                state = await get_or_create_state(chat_id)
                state.current_chapter = ch
                state.current_verse = v
                await save_state(state)
                await update.message.reply_text(f"✅ Next shloka set: Chapter {ch}, Verse {v}")
            else:
                await update.message.reply_text("❌ Invalid chapter/verse number.")
        except ValueError:
            await update.message.reply_text("❌ Usage: /setshlok 2 47")
    else:
        await update.message.reply_text("❌ Usage: /setshlok 2 47")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    state = await get_or_create_state(chat_id)
    await update.message.reply_text(
        f"📊 *Status:*\n"
        f"Chapter: {state.current_chapter}\n"
        f"Verse: {state.current_verse}\n"
        f"Day: {state.day_count}\n"
        f"Active: {'Yes ✅' if state.is_active else 'No ❌'}",
        parse_mode="Markdown",
    )
