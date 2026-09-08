from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from bookings.models import (
    Booking,
    BookingSeat,
    Payment,
    SeatReservation,
)
from tickets.models import Ticket
from tickets.services import create_ticket


class Command(BaseCommand):
    help = (
        "Backfill missing SeatReservation records and "
        "Tickets for existing successful payments."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: no database changes will be made."
                )
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "CineFlow Booking Data Backfill"
            )
        )
        self.stdout.write("")

        reservation_stats = self.backfill_seat_reservations(
            dry_run=dry_run
        )

        self.stdout.write("")

        ticket_stats = self.backfill_tickets(
            dry_run=dry_run
        )

        self.stdout.write("")
        self.print_summary(
            reservation_stats,
            ticket_stats,
            dry_run,
        )

    def backfill_seat_reservations(self, dry_run=False):
        stats = {
            "created": 0,
            "existing": 0,
            "skipped_expired": 0,
            "conflicts": 0,
        }

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "1. Seat Reservations"
            )
        )

        active_bookings = (
            Booking.objects
            .filter(
                status__in=[
                    Booking.Status.HELD,
                    Booking.Status.CONFIRMED,
                ]
            )
            .select_related("showtime")
            .prefetch_related("booking_seats")
            .order_by("id")
        )

        for booking in active_bookings:
            # A held booking whose hold has already expired
            # should not become an active seat reservation.
            if (
                booking.status == Booking.Status.HELD
                and booking.hold_expires_at
                and booking.hold_expires_at <= timezone.now()
            ):
                stats["skipped_expired"] += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"  SKIPPED expired hold: "
                        f"{booking.booking_reference}"
                    )
                )
                continue

            booking_seats = booking.booking_seats.all()

            for booking_seat in booking_seats:
                existing = (
                    SeatReservation.objects
                    .filter(
                        showtime_id=booking.showtime_id,
                        seat_id=booking_seat.seat_id,
                    )
                    .first()
                )

                if existing:
                    if existing.booking_id == booking.id:
                        stats["existing"] += 1
                    else:
                        stats["conflicts"] += 1

                        self.stdout.write(
                            self.style.ERROR(
                                f"  CONFLICT: "
                                f"{booking.booking_reference} "
                                f"cannot reserve seat "
                                f"{booking_seat.seat_id} "
                                f"for showtime "
                                f"{booking.showtime_id}; "
                                f"already reserved by booking "
                                f"{existing.booking.booking_reference}"
                            )
                        )

                    continue

                if dry_run:
                    stats["created"] += 1

                    self.stdout.write(
                        f"  WOULD CREATE reservation: "
                        f"{booking.booking_reference} "
                        f"→ seat {booking_seat.seat_id}"
                    )
                    continue

                try:
                    with transaction.atomic():
                        reservation = SeatReservation.objects.create(
                            booking_id=booking.id,
                            showtime_id=booking.showtime_id,
                            seat_id=booking_seat.seat_id,
                        )

                    stats["created"] += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  CREATED reservation: "
                            f"{booking.booking_reference} "
                            f"→ seat {booking_seat.seat_id}"
                        )
                    )

                except IntegrityError:
                    # Another reservation may have been created
                    # between our check and insert.
                    existing = (
                        SeatReservation.objects
                        .filter(
                            showtime_id=booking.showtime_id,
                            seat_id=booking_seat.seat_id,
                        )
                        .select_related("booking")
                        .first()
                    )

                    if existing and existing.booking_id == booking.id:
                        stats["existing"] += 1
                    else:
                        stats["conflicts"] += 1

                        self.stdout.write(
                            self.style.ERROR(
                                f"  CONFLICT: "
                                f"{booking.booking_reference} "
                                f"→ seat {booking_seat.seat_id}"
                            )
                        )

        return stats

    def backfill_tickets(self, dry_run=False):
        stats = {
            "created": 0,
            "existing": 0,
            "skipped": 0,
            "errors": 0,
        }

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "2. Digital Tickets"
            )
        )

        successful_payments = (
            Payment.objects
            .filter(status=Payment.Status.SUCCESSFUL)
            .select_related("booking")
            .order_by("id")
        )

        for payment in successful_payments:
            booking = payment.booking

            existing_ticket = (
                Ticket.objects
                .filter(booking_id=booking.id)
                .first()
            )

            if existing_ticket:
                stats["existing"] += 1
                continue

            # A successful payment should normally belong to
            # a confirmed booking. Do not manufacture tickets
            # for inconsistent historical records.
            if booking.status != Booking.Status.CONFIRMED:
                stats["skipped"] += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"  SKIPPED ticket: "
                        f"{payment.payment_reference} → "
                        f"{booking.booking_reference} "
                        f"(booking status: "
                        f"{booking.get_status_display()})"
                    )
                )
                continue

            if dry_run:
                stats["created"] += 1

                self.stdout.write(
                    f"  WOULD CREATE ticket: "
                    f"{booking.booking_reference}"
                )
                continue

            try:
                with transaction.atomic():
                    # Lock the booking so another process cannot
                    # simultaneously create the same ticket.
                    locked_booking = (
                        Booking.objects
                        .select_for_update()
                        .get(pk=booking.id)
                    )

                    # Check again after acquiring the lock.
                    if Ticket.objects.filter(
                        booking_id=locked_booking.id
                    ).exists():
                        stats["existing"] += 1
                        continue

                    ticket = create_ticket(locked_booking)

                stats["created"] += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  CREATED ticket: "
                        f"{locked_booking.booking_reference} "
                        f"→ {ticket.ticket_number}"
                    )
                )

            except IntegrityError as exc:
                stats["errors"] += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"  ERROR creating ticket for "
                        f"{booking.booking_reference}: {exc}"
                    )
                )

            except Exception as exc:
                stats["errors"] += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"  ERROR creating ticket for "
                        f"{booking.booking_reference}: {exc}"
                    )
                )

        return stats

    def print_summary(
        self,
        reservation_stats,
        ticket_stats,
        dry_run,
    ):
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Backfill Summary"
            )
        )

        self.stdout.write("")
        self.stdout.write("Seat Reservations:")
        self.stdout.write(
            f"  Created: {reservation_stats['created']}"
        )
        self.stdout.write(
            f"  Already existed: {reservation_stats['existing']}"
        )
        self.stdout.write(
            f"  Expired holds skipped: "
            f"{reservation_stats['skipped_expired']}"
        )
        self.stdout.write(
            f"  Conflicts: {reservation_stats['conflicts']}"
        )

        self.stdout.write("")
        self.stdout.write("Digital Tickets:")
        self.stdout.write(
            f"  Created: {ticket_stats['created']}"
        )
        self.stdout.write(
            f"  Already existed: {ticket_stats['existing']}"
        )
        self.stdout.write(
            f"  Skipped: {ticket_stats['skipped']}"
        )
        self.stdout.write(
            f"  Errors: {ticket_stats['errors']}"
        )

        self.stdout.write("")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN complete. No changes were made."
                )
            )
        elif (
            reservation_stats["conflicts"] == 0
            and ticket_stats["errors"] == 0
        ):
            self.stdout.write(
                self.style.SUCCESS(
                    "Backfill completed successfully."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Backfill completed with conflicts/errors. "
                    "Review the messages above."
                )
            )