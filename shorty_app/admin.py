from django.contrib import admin
from .models import Url, FlaggedUrlAttempt


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'original_url']


admin.site.register(FlaggedUrlAttempt)