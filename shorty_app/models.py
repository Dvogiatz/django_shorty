from django.db import models
from django.utils import timezone
from datetime import timedelta

# Helper functions
def default_expiration():
    return timezone.now() + timedelta(days=7)


# Create your models here.
class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

class Url(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiration, db_index=True)

    def __str__(self):
        return self.short_code