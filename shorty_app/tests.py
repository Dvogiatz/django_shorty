from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import UrlForm
from .models import Url


class UrlModelTests(TestCase):
    def test_default_expiration_is_about_a_week_out(self):
        url = Url.objects.create(original_url="https://example.com", short_code="abc123")
        delta = url.expires_at - url.created_at
        self.assertAlmostEqual(delta.total_seconds(), timedelta(days=7).total_seconds(), delta=5)

    def test_short_code_must_be_unique(self):
        Url.objects.create(original_url="https://example.com", short_code="dup123")
        with self.assertRaises(Exception):
            Url.objects.create(original_url="https://other.com", short_code="dup123")


class EnforceCapacityTests(TestCase):
    def _make(self, short_code, created_days_ago=0, expired=False):
        url = Url.objects.create(original_url="https://example.com", short_code=short_code)
        updates = {"created_at": timezone.now() - timedelta(days=created_days_ago)}
        if expired:
            updates["expires_at"] = timezone.now() - timedelta(days=1)
        Url.objects.filter(pk=url.pk).update(**updates)
        return url

    @override_settings(MAX_URLS=3)
    def test_under_capacity_does_nothing(self):
        self._make("a1")
        self._make("a2")
        Url.enforce_capacity()
        self.assertEqual(Url.objects.count(), 2)

    @override_settings(MAX_URLS=3)
    def test_at_capacity_deletes_expired_first(self):
        self._make("b1", created_days_ago=3, expired=True)
        self._make("b2", created_days_ago=2)
        self._make("b3", created_days_ago=1)
        Url.enforce_capacity()
        remaining = set(Url.objects.values_list("short_code", flat=True))
        self.assertEqual(remaining, {"b2", "b3"})

    @override_settings(MAX_URLS=3)
    def test_at_capacity_with_no_expired_evicts_oldest(self):
        self._make("c1", created_days_ago=3)
        self._make("c2", created_days_ago=2)
        self._make("c3", created_days_ago=1)
        Url.enforce_capacity()
        remaining = set(Url.objects.values_list("short_code", flat=True))
        self.assertEqual(remaining, {"c2", "c3"})


class UrlFormTests(TestCase):
    def test_valid_url_passes(self):
        form = UrlForm({"original_url": "https://example.com/page"})
        self.assertTrue(form.is_valid())

    def test_invalid_url_is_rejected(self):
        form = UrlForm({"original_url": "not-a-url"})
        self.assertFalse(form.is_valid())


class ShortenViewTests(TestCase):
    def test_get_shows_empty_form(self):
        response = self.client.get(reverse("shorty"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a URL to shorten")

    def test_post_valid_url_creates_short_link(self):
        response = self.client.post(reverse("shorty"), {"original_url": "https://example.com/page"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Url.objects.count(), 1)
        url = Url.objects.first()
        self.assertContains(response, f"/shorty/{url.short_code}/")

    def test_post_invalid_url_does_not_create_short_link(self):
        response = self.client.post(reverse("shorty"), {"original_url": "not-a-url"})
        self.assertEqual(Url.objects.count(), 0)
        self.assertContains(response, "Enter a valid URL.")

    @override_settings(MAX_URLS=2)
    def test_post_at_capacity_evicts_to_stay_under_cap(self):
        Url.objects.create(original_url="https://example.com/1", short_code="old001")
        Url.objects.filter(short_code="old001").update(created_at=timezone.now() - timedelta(days=1))
        Url.objects.create(original_url="https://example.com/2", short_code="old002")
        response = self.client.post(reverse("shorty"), {"original_url": "https://example.com/3"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Url.objects.count(), 2)
        self.assertFalse(Url.objects.filter(short_code="old001").exists())


class RedirectViewTests(TestCase):
    def test_valid_code_redirects_to_original_url(self):
        Url.objects.create(original_url="https://example.com/page", short_code="valid1")
        response = self.client.get(reverse("redirect_short_url", args=["valid1"]))
        self.assertRedirects(response, "https://example.com/page", fetch_redirect_response=False)

    def test_unknown_code_returns_404(self):
        response = self.client.get(reverse("redirect_short_url", args=["missing"]))
        self.assertEqual(response.status_code, 404)

    def test_expired_code_returns_404_and_deletes_row(self):
        url = Url.objects.create(original_url="https://example.com/page", short_code="expired1")
        Url.objects.filter(pk=url.pk).update(expires_at=timezone.now() - timedelta(days=1))
        response = self.client.get(reverse("redirect_short_url", args=["expired1"]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Url.objects.filter(pk=url.pk).exists())
