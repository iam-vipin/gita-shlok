from django.contrib import admin
from .models import BotState, VerseHistory


@admin.register(BotState)
class BotStateAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "current_chapter", "current_verse", "day_count", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("chat_id",)


@admin.register(VerseHistory)
class VerseHistoryAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "chapter", "verse", "sent_at")
    list_filter = ("chapter",)
    search_fields = ("chat_id",)
    readonly_fields = ("sent_at",)
