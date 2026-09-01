import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


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

    return bool(result.get("matches"))
