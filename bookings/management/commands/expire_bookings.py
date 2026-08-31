from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking
from bookings.services import expire_booking


class Command(BaseCommand):

    help = (
        "Expire booking holds whose hold expiration "
        "time has passed."
    )

    def handle(self, *args, **options):

        now = timezone.now()

        expired_bookings = (
            Booking.objects
            .filter(
                status=Booking.Status.HELD,
                hold_expires_at__isnull=False,
                hold_expires_at__lte=now,
            )
            .only(
                "id",
                "hold_expires_at",
            )
        )

        count = 0

        for booking in expired_bookings:

            expire_booking(booking)

            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {count} booking hold(s)."
            )
        )