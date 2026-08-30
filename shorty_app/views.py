from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.utils import timezone
from django.http import Http404
from .models import TodoItem, Url
from .forms import UrlForm
import random
import string


# Helper functions
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not Url.objects.filter(short_code=code).exists():
            return code

# Create your views here.
def home(request):
    return render(request, "home.html")

def todos(request):
    items = TodoItem.objects.all()
    return render(request, "todos.html", {"todos": items})

def shorty(request):
    short_url = None
    if request.method == "POST":
        form = UrlForm(request.POST)
        if form.is_valid():
            url = form.save(commit=False)
            url.short_code = generate_short_code()
            url.save()
            short_url = request.build_absolute_uri(f"/shorty/{url.short_code}/")
            form = UrlForm()
    else:
        form = UrlForm()
    return render(request, "shorty.html", {"form": form, "short_url": short_url})

def redirect_short_url(request, short_code):
    url = get_object_or_404(Url, short_code=short_code)
    if url.expires_at < timezone.now():
        url.delete()
        raise Http404
    return redirect(url.original_url)