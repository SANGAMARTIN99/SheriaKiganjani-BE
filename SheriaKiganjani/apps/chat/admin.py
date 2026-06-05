from django.contrib import admin
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'title', 'started_at', 'language')
    list_filter = ('language', 'started_at')
    search_fields = ('title', 'user__username', 'session_id')
    inlines = [ChatMessageInline]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at', 'rating')
    list_filter = ('role', 'rating', 'created_at')
    search_fields = ('content', 'session__title')
