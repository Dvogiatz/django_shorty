from django.contrib import admin
from .models import Url, FlaggedUrlAttempt

# Register your models here.
admin.site.register(Url)
admin.site.register(FlaggedUrlAttempt)