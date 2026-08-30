from datetime import timedelta

from django.test import TestCase
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
