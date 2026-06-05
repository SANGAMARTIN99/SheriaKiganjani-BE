from django.contrib import admin
from .models import SearchTopic

@admin.register(SearchTopic)
class SearchTopicAdmin(admin.ModelAdmin):
    list_display = ('topic_name', 'count', 'last_requested')
    search_fields = ('topic_name',)
    ordering = ('-count',)
