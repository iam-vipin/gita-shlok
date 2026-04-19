from django.db import models


class BotState(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)
    current_chapter = models.IntegerField(default=1)
    current_verse = models.IntegerField(default=1)
    day_count = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bot State"
        verbose_name_plural = "Bot States"

    def __str__(self):
        return f"Chat {self.chat_id} - Ch{self.current_chapter}:{self.current_verse} (Day {self.day_count})"


class VerseHistory(models.Model):
    chat_id = models.CharField(max_length=100)
    chapter = models.IntegerField()
    verse = models.IntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Verse History"
        verbose_name_plural = "Verse Histories"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Ch{self.chapter}:{self.verse} → {self.chat_id} at {self.sent_at}"
