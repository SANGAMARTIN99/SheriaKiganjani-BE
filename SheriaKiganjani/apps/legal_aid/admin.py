from django.contrib import admin
from .models import LegalAidOrganization

@admin.register(LegalAidOrganization)
class LegalAidOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'phone', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description', 'email', 'phone')
