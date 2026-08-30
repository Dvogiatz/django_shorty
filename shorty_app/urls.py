from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("shorty/", views.shorty, name="shorty"),
    path("shorty/<str:short_code>/", views.redirect_short_url, name="redirect_short_url"),
]