from collections import Counter
from urllib.parse import urlparse

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from shorty_app.models import FlaggedUrlAttempt


class Command(BaseCommand):
    help = "Email a daily aggregated report of Safe-Browsing-flagged URL attempts, then clear them."

    def handle(self, *args, **options):
        attempts = list(FlaggedUrlAttempt.objects.order_by("created_at"))

        if not attempts:
            self.stdout.write("No flagged URL attempts to report.")
            return

        if not settings.REPORT_RECIPIENT_EMAIL:
            self.stdout.write(self.style.WARNING(
                "REPORT_RECIPIENT_EMAIL is not configured; skipping report "
                f"({len(attempts)} flagged attempt(s) left in place for next run)."
            ))
            return

        domain_counts = Counter(urlparse(a.url).hostname or "unknown" for a in attempts)
        domain_lines = "\n".join(
            f"  {domain}: {count}" for domain, count in domain_counts.most_common()
        )
        url_lines = "\n".join(
            f"  {a.created_at:%Y-%m-%d %H:%M UTC} — {a.url}" for a in attempts
        )

        subject = f"Shorty: {len(attempts)} unsafe URL(s) blocked"
        body = (
            f"{len(attempts)} URL(s) were rejected by the Safe Browsing check "
            f"since the last report.\n\n"
            f"By domain:\n{domain_lines}\n\n"
            f"Details:\n{url_lines}\n"
        )

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.REPORT_RECIPIENT_EMAIL],
        )

        FlaggedUrlAttempt.objects.filter(pk__in=[a.pk for a in attempts]).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Sent report for {len(attempts)} flagged attempt(s) and cleared them."
        ))
