from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

# Helper functions
def default_expiration():
    return timezone.now() + timedelta(days=7)


# Create your models here.
class Url(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiration, db_index=True)

    def __str__(self):
        return self.short_code

    @classmethod
    def enforce_capacity(cls):
        max_urls = settings.MAX_URLS
        if cls.objects.count() < max_urls:
            return
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
        if cls.objects.count() >= max_urls:
            oldest = cls.objects.order_by('created_at').first()
            if oldest:
                oldest.delete()


class FlaggedUrlAttempt(models.Model):
    url = models.URLField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url