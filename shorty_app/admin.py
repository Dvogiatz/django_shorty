from django.contrib import admin
from .models import TodoItem,Url

# Register your models here.
admin.site.register(TodoItem)
admin.site.register(Url)