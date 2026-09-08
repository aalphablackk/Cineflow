from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking

from .models import Ticket

import secrets


# ============================================================
# TICKET NUMBER
# ============================================================

def generate_ticket_number():
    return f"CF-TKT-{secrets.token_hex(5).upper()}"


# ============================================================
# TICKET CODE
# ============================================================

def generate_ticket_code():
    return secrets.token_urlsafe(24)


# ============================================================
# CREATE TICKET
# ============================================================

def create_ticket(booking):
    """
    Create a digital ticket for a confirmed booking.

    A booking can only have one ticket.
    """

    if booking.status != Booking.Status.CONFIRMED:
        raise ValidationError(
            "A ticket can only be created for a confirmed booking."
        )

    ticket, created = Ticket.objects.get_or_create(
        booking=booking,
        defaults={
            "ticket_number": generate_ticket_number(),
            "ticket_code": generate_ticket_code(),
        },
    )

    return ticket


# ============================================================
# VERIFY TICKET
# ============================================================

@transaction.atomic
def verify_ticket(ticket_code):
    """
    Verify a digital ticket.

    A ticket is valid only when:

    - The ticket exists.
    - The ticket is marked valid.
    - The booking is confirmed.
    - The ticket has not already been used.

    The ticket is locked while being verified so that
    simultaneous verification attempts cannot both admit
    the same ticket.
    """

    try:

        ticket = (
            Ticket.objects
            .select_for_update()
            .select_related(
                "booking",
                "booking__user",
                "booking__showtime",
                "booking__showtime__movie",
                "booking__showtime__screen",
                "booking__showtime__screen__cinema",
            )
            .prefetch_related(
                "booking__booking_seats__seat",
            )
            .get(
                ticket_code=ticket_code,
            )
        )

    except Ticket.DoesNotExist:

        raise ValidationError(
            "Ticket not found. Please check the ticket code."
        )


    # --------------------------------------------------------
    # 1. Check ticket validity
    # --------------------------------------------------------

    if not ticket.is_valid:

        raise ValidationError(
            "This ticket is no longer valid."
        )


    # --------------------------------------------------------
    # 2. Check booking status
    # --------------------------------------------------------

    if ticket.booking.status != Booking.Status.CONFIRMED:

        raise ValidationError(
            "This ticket is not associated with a confirmed booking."
        )


    # --------------------------------------------------------
    # 3. Check whether ticket was already used
    # --------------------------------------------------------

    if ticket.used_at is not None:

        raise ValidationError(
            "This ticket has already been used."
        )


    return ticket


# ============================================================
# USE TICKET
# ============================================================

@transaction.atomic
def use_ticket(ticket_code):
    """
    Verify and mark a ticket as used.

    The ticket is locked during the operation to prevent
    duplicate admission from simultaneous requests.
    """

    try:

        ticket = (
            Ticket.objects
            .select_for_update()
            .select_related(
                "booking",
                "booking__user",
                "booking__showtime",
                "booking__showtime__movie",
                "booking__showtime__screen",
                "booking__showtime__screen__cinema",
            )
            .prefetch_related(
                "booking__booking_seats__seat",
            )
            .get(
                ticket_code=ticket_code,
            )
        )

    except Ticket.DoesNotExist:

        raise ValidationError(
            "Ticket not found. Please check the ticket code."
        )


    # --------------------------------------------------------
    # 1. Check ticket validity
    # --------------------------------------------------------

    if not ticket.is_valid:

        raise ValidationError(
            "This ticket is no longer valid."
        )


    # --------------------------------------------------------
    # 2. Check booking status
    # --------------------------------------------------------

    if ticket.booking.status != Booking.Status.CONFIRMED:

        raise ValidationError(
            "This ticket is not associated with a confirmed booking."
        )


    # --------------------------------------------------------
    # 3. Prevent duplicate admission
    # --------------------------------------------------------

    if ticket.used_at is not None:

        raise ValidationError(
            "This ticket has already been used."
        )


    # --------------------------------------------------------
    # 4. Mark ticket as used
    # --------------------------------------------------------

    ticket.used_at = timezone.now()

    ticket.save(
        update_fields=[
            "used_at",
            "updated_at",
        ],
    )


    return ticket