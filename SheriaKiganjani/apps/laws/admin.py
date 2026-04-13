from django.contrib import admin
from .models import LawProvision
from django.utils.translation import gettext_lazy as _

@admin.register(LawProvision)
class LawProvisionAdmin(admin.ModelAdmin):
    list_display = ('law_name', 'article_no', 'category', 'scope', 'is_active', 'last_amended')
    list_filter = ('category', 'scope', 'is_active')
    search_fields = ('law_name', 'article_no', 'content_official_en', 'content_official_sw')
    
    fieldsets = (
        (_('Identity'), {
            'fields': ('law_name', 'article_no', 'category')
        }),
        (_('Official Text'), {
            'fields': ('content_official_en', 'content_official_sw')
        }),
        (_('Mtaani Summaries'), {
            'fields': ('plain_summary_en', 'plain_summary_sw', 'good_conduct', 'penalty_summary')
        }),
        (_('Scope & Status'), {
            'fields': ('scope', 'region', 'last_amended', 'is_active')
        }),
    )
