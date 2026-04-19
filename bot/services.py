import random
import logging
import requests

logger = logging.getLogger(__name__)

API_BASE = "https://vedicscriptures.github.io"

CHAPTERS = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28, 9: 34,
    10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78,
}
TOTAL_VERSES = 700


def get_verse_number(chapter, verse):
    """Get absolute verse number (1-700) from chapter and verse."""
    count = 0
    for ch in range(1, chapter):
        count += CHAPTERS[ch]
    return count + verse


def fetch_verse_data(chapter, verse):
    """Fetch complete verse data from vedicscriptures API."""
    try:
        resp = requests.get(f"{API_BASE}/slok/{chapter}/{verse}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error fetching verse {chapter}:{verse}: {e}")
    return None


def format_verse_message(chapter, verse, day_count=None):
    """Fetch and format a complete verse message."""
    data = fetch_verse_data(chapter, verse)

    if not data:
        return None

    verse_num = get_verse_number(chapter, verse)
    shloka = data.get("slok", "")

    # Hindi translation (Swami Tejomayananda or Swami Ramsukhdas)
    hindi = None
    for key in ("tej", "rams", "spiegel"):
        author_data = data.get(key, {})
        if author_data and author_data.get("ht"):
            hindi = author_data["ht"]
            break

    # English translation (prefer Swami Sivananda, Purohit Swami, Prabhupada)
    english = None
    for key in ("siva", "purohit", "prabhu", "gambir", "adi", "san", "raman", "abhinav"):
        author_data = data.get(key, {})
        if author_data and author_data.get("et"):
            english = author_data["et"]
            break

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
    footer = f"📖 Verse {verse_num}/{TOTAL_VERSES}"
    if day_count:
        footer += f" | Day {day_count}"
    msg += footer

    return msg


def next_verse(chapter, verse):
    """Get the next chapter and verse, wrapping around after 18:78."""
    if verse < CHAPTERS[chapter]:
        return chapter, verse + 1
    elif chapter < 18:
        return chapter + 1, 1
    else:
        return 1, 1


DAILY_COUNT = 5


def get_batch_verses(chapter, verse, count=DAILY_COUNT):
    """Get a list of (chapter, verse) tuples starting from the given position."""
    verses = [(chapter, verse)]
    ch, v = chapter, verse
    for _ in range(count - 1):
        ch, v = next_verse(ch, v)
        verses.append((ch, v))
    return verses


def random_verse():
    """Get a random chapter and verse."""
    chapter = random.randint(1, 18)
    verse = random.randint(1, CHAPTERS[chapter])
    return chapter, verse
