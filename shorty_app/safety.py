import json
import logging
import urllib.error
import urllib.request
from urllib.parse import urlparse

from django.conf import settings

from .models import FlaggedUrlAttempt

logger = logging.getLogger(__name__)

SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

# Common URL shorteners. Allowing these as a shorten target lets someone chain
# shorteners to hide the real destination from review (including from the
# Safe Browsing check above, which only sees the immediate target).
KNOWN_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "adf.ly", "bit.do", "mcaf.ee", "tiny.cc", "rebrand.ly", "cutt.ly",
    "shorte.st", "s.id", "v.gd", "rb.gy", "tr.im", "x.co", "qr.ae", "u.to",
    "shorturl.at", "clck.ru", "soo.gd", "snip.ly", "po.st", "tny.im",
}


def is_url_from_another_shortener(url):
    """Reject destinations that are themselves URL shorteners, since
    chaining shorteners is a common way to hide a malicious destination
    from review."""
    hostname = (urlparse(url).hostname or "").lower()
    hostname = hostname.removeprefix("www.")
    return hostname in KNOWN_SHORTENER_DOMAINS


def is_url_flagged_unsafe(url):
    """Check a URL against Google Safe Browsing. Fails open (returns False)
    if no API key is configured, or if the check itself errors out — a
    best-effort screen, not a hard dependency for the app to function."""
    api_key = getattr(settings, "SAFE_BROWSING_API_KEY", "")
    if not api_key:
        return False

    payload = {
        "client": {"clientId": "django-shorty", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    request = urllib.request.Request(
        f"{SAFE_BROWSING_ENDPOINT}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        logger.warning("Safe Browsing check failed, allowing URL through: %s", exc)
        return False

    is_flagged = bool(result.get("matches"))
    if is_flagged:
        FlaggedUrlAttempt.objects.create(url=url)
    return is_flagged
