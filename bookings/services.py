from datetime import timedelta
import secrets

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from cinemas.models import Seat
from showtimes.models import Showtime

from .models import Booking, BookingSeat


# ============================================================
# CONFIGURATION
# ============================================================

HOLD_DURATION_MINUTES = 1


# ============================================================
# BOOKING REFERENCE
# ============================================================

def generate_booking_reference():
    """
    Generate a unique CineFlow booking reference.
    """

    return f"CF-{secrets.token_hex(5).upper()}"


# ============================================================
# AVAILABLE SEATS
# ============================================================

def get_available_seats(showtime):
    """
    Return all currently available seats for an
    assigned-seating showtime.

    Confirmed bookings and active holds both
    make seats unavailable.
    """

    now = timezone.now()

    confirmed_seat_ids = (
        BookingSeat.objects
        .filter(
            showtime=showtime,
            booking__status=Booking.Status.CONFIRMED,
        )
        .values_list(
            "seat_id",
            flat=True,
        )
    )

    held_seat_ids = (
        BookingSeat.objects
        .filter(
            showtime=showtime,
            booking__status=Booking.Status.HELD,
            booking__hold_expires_at__gt=now,
        )
        .values_list(
            "seat_id",
            flat=True,
        )
    )

    occupied_seat_ids = set(
        confirmed_seat_ids
    )

    occupied_seat_ids.update(
        held_seat_ids
    )

    return (
        Seat.objects
        .filter(
            screen=showtime.screen,
            is_active=True,
        )
        .exclude(
            id__in=occupied_seat_ids,
        )
        .order_by(
            "row",
            "number",
        )
    )


# ============================================================
# SEAT MAP
# ============================================================

def get_seat_map(showtime):
    """
    Return all active seats for the showtime's screen,
    together with their current availability status.

    This is used by the frontend to build the cinema
    seat map.
    """

    now = timezone.now()

    occupied_seat_ids = set(
        BookingSeat.objects
        .filter(
            showtime=showtime,
        )
        .filter(
            models.Q(
                booking__status=Booking.Status.CONFIRMED,
            )
            |
            models.Q(
                booking__status=Booking.Status.HELD,
                booking__hold_expires_at__gt=now,
            )
        )
        .values_list(
            "seat_id",
            flat=True,
        )
    )

    seats = (
        Seat.objects
        .filter(
            screen=showtime.screen,
            is_active=True,
        )
        .order_by(
            "row",
            "number",
        )
    )

    return [
        {
            "seat": seat,
            "is_available": (
                seat.id not in occupied_seat_ids
            ),
        }
        for seat in seats
    ]


# ============================================================
# AVAILABLE SEAT COUNT
# ============================================================

def get_available_seat_count(showtime):
    """
    Return the number of seats currently available
    for an assigned-seating showtime.
    """

    return get_available_seats(
        showtime
    ).count()


# ============================================================
# AVAILABLE GENERAL-ADMISSION CAPACITY
# ============================================================

def get_available_capacity(showtime):
    """
    Return the number of tickets currently available
    for a general-admission showtime.

    Confirmed bookings and active holds both
    consume capacity.
    """

    now = timezone.now()

    confirmed_tickets = (
        Booking.objects
        .filter(
            showtime=showtime,
            status=Booking.Status.CONFIRMED,
        )
        .aggregate(
            total=models.Sum(
                "ticket_quantity"
            )
        )["total"]
        or 0
    )

    held_tickets = (
        Booking.objects
        .filter(
            showtime=showtime,
            status=Booking.Status.HELD,
            hold_expires_at__gt=now,
        )
        .aggregate(
            total=models.Sum(
                "ticket_quantity"
            )
        )["total"]
        or 0
    )

    available_capacity = (
        showtime.screen.capacity
        - confirmed_tickets
        - held_tickets
    )

    return max(
        available_capacity,
        0,
    )


# ============================================================
# CREATE ASSIGNED-SEATING HOLD
# ============================================================

@transaction.atomic
def create_assigned_hold(
    *,
    user,
    showtime,
    seat_ids,
):
    """
    Temporarily hold selected seats.

    Seats remain unavailable while the customer
    completes payment.

    The AssignedBookingForm uses a
    ModelMultipleChoiceField, so seat_ids initially
    contains Seat objects. They are converted into
    database IDs before querying.
    """

    # --------------------------------------------------------
    # 1. Lock the showtime
    # --------------------------------------------------------

    showtime = (
        Showtime.objects
        .select_for_update()
        .select_related(
            "movie",
            "screen",
        )
        .get(
            pk=showtime.pk,
        )
    )

    # --------------------------------------------------------
    # 2. Validate showtime
    # --------------------------------------------------------

    if showtime.status != Showtime.Status.SCHEDULED:

        raise ValidationError(
            "This showtime is no longer available for booking."
        )

    if showtime.booking_mode != Showtime.BookingMode.ASSIGNED:

        raise ValidationError(
            "This showtime uses general admission. "
            "Please select the number of tickets instead."
        )

    # --------------------------------------------------------
    # 3. Validate seat selection
    # --------------------------------------------------------

    if not seat_ids:

        raise ValidationError(
            "Please select at least one seat to continue."
        )

    # --------------------------------------------------------
    # 4. Convert Seat objects to IDs
    # --------------------------------------------------------

    seat_ids = list(
        {
            seat.id
            for seat in seat_ids
        }
    )

    # --------------------------------------------------------
    # 5. Lock requested seats
    # --------------------------------------------------------

    seats = list(
        Seat.objects
        .select_for_update()
        .filter(
            id__in=seat_ids,
            screen=showtime.screen,
            is_active=True,
        )
    )

    # --------------------------------------------------------
    # 6. Validate every requested seat
    # --------------------------------------------------------

    if len(seats) != len(seat_ids):

        raise ValidationError(
            "One or more of your selected seats are "
            "invalid or unavailable. Please review "
            "your seat selection and try again."
        )

    # --------------------------------------------------------
    # 7. Expire old holds
    # --------------------------------------------------------

    expire_holds_for_showtime(
        showtime
    )

    # --------------------------------------------------------
    # 8. Check whether requested seats are occupied
    # --------------------------------------------------------

    now = timezone.now()

    occupied_seat_ids = set(
        BookingSeat.objects
        .filter(
            showtime=showtime,
            seat_id__in=seat_ids,
        )
        .filter(
            models.Q(
                booking__status=Booking.Status.CONFIRMED,
            )
            |
            models.Q(
                booking__status=Booking.Status.HELD,
                booking__hold_expires_at__gt=now,
            )
        )
        .values_list(
            "seat_id",
            flat=True,
        )
    )

    if occupied_seat_ids:

        raise ValidationError(
            "One or more of your selected seats are "
            "no longer available. Please choose different "
            "seats and try again."
        )

    # --------------------------------------------------------
    # 9. Calculate booking details
    # --------------------------------------------------------

    ticket_quantity = len(
        seats
    )

    total_amount = (
        showtime.ticket_price
        * ticket_quantity
    )

    hold_expires_at = (
        timezone.now()
        + timedelta(
            minutes=HOLD_DURATION_MINUTES,
        )
    )

    # --------------------------------------------------------
    # 10. Create temporary booking
    # --------------------------------------------------------

    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        booking_reference=generate_booking_reference(),
        ticket_quantity=ticket_quantity,
        total_amount=total_amount,
        status=Booking.Status.HELD,
        hold_expires_at=hold_expires_at,
    )

    # --------------------------------------------------------
    # 11. Create BookingSeat records
    # --------------------------------------------------------

    booking_seats = [
        BookingSeat(
            booking=booking,
            showtime=showtime,
            seat=seat,
            price=showtime.ticket_price,
        )
        for seat in seats
    ]

    BookingSeat.objects.bulk_create(
        booking_seats
    )

    return booking


# ============================================================
# CREATE GENERAL-ADMISSION HOLD
# ============================================================

@transaction.atomic
def create_general_hold(
    *,
    user,
    showtime,
    ticket_quantity,
):
    """
    Temporarily reserve general-admission capacity.
    """

    # --------------------------------------------------------
    # 1. Lock the showtime
    # --------------------------------------------------------

    showtime = (
        Showtime.objects
        .select_for_update()
        .select_related(
            "movie",
            "screen",
        )
        .get(
            pk=showtime.pk,
        )
    )

    # --------------------------------------------------------
    # 2. Validate showtime
    # --------------------------------------------------------

    if showtime.status != Showtime.Status.SCHEDULED:

        raise ValidationError(
            "This showtime is no longer available for booking."
        )

    if showtime.booking_mode != Showtime.BookingMode.GENERAL:

        raise ValidationError(
            "This showtime uses assigned seating. "
            "Please select your seats instead."
        )

    # --------------------------------------------------------
    # 3. Validate quantity
    # --------------------------------------------------------

    if not isinstance(
        ticket_quantity,
        int,
    ):

        raise ValidationError(
            "Please enter a valid number of tickets."
        )

    if ticket_quantity <= 0:

        raise ValidationError(
            "Please select at least one ticket."
        )

    # --------------------------------------------------------
    # 4. Expire old holds
    # --------------------------------------------------------

    expire_holds_for_showtime(
        showtime
    )

    # --------------------------------------------------------
    # 5. Check available capacity
    # --------------------------------------------------------

    available_capacity = (
        get_available_capacity(
            showtime
        )
    )

    if ticket_quantity > available_capacity:

        if available_capacity == 0:

            raise ValidationError(
                "Sorry, this showtime is currently sold out."
            )

        raise ValidationError(
            f"Only {available_capacity} ticket(s) "
            "are currently available. Please reduce "
            "the number of tickets and try again."
        )

    # --------------------------------------------------------
    # 6. Calculate price on the server
    # --------------------------------------------------------

    total_amount = (
        showtime.ticket_price
        * ticket_quantity
    )

    hold_expires_at = (
        timezone.now()
        + timedelta(
            minutes=HOLD_DURATION_MINUTES,
        )
    )

    # --------------------------------------------------------
    # 7. Create temporary booking
    # --------------------------------------------------------

    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        booking_reference=generate_booking_reference(),
        ticket_quantity=ticket_quantity,
        total_amount=total_amount,
        status=Booking.Status.HELD,
        hold_expires_at=hold_expires_at,
    )

    return booking


# ============================================================
# CONFIRM BOOKING
# ============================================================

@transaction.atomic
def confirm_booking(booking):
    """
    Confirm a held booking after successful payment.
    """

    booking = (
        Booking.objects
        .select_for_update()
        .select_related(
            "showtime",
        )
        .get(
            pk=booking.pk,
        )
    )

    # --------------------------------------------------------
    # 1. Validate booking status
    # --------------------------------------------------------

    if booking.status != Booking.Status.HELD:

        raise ValidationError(
            "This booking is no longer available for payment."
        )

    # --------------------------------------------------------
    # 2. Validate hold expiration
    # --------------------------------------------------------

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at <= timezone.now()
    ):

        booking.status = Booking.Status.EXPIRED

        booking.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        raise ValidationError(
            "Your booking hold has expired. "
            "Please start a new booking."
        )

    # --------------------------------------------------------
    # 3. Confirm booking
    # --------------------------------------------------------

    booking.status = Booking.Status.CONFIRMED

    booking.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    return booking


# ============================================================
# EXPIRE A BOOKING
# ============================================================


@transaction.atomic
def expire_booking(booking):
    """
    Expire a booking whose hold period has ended
    and release its temporarily held seats.
    """

    booking = (
        Booking.objects
        .select_for_update()
        .get(
            pk=booking.pk,
        )
    )

    if booking.status != Booking.Status.HELD:
        return booking

    if (
        booking.hold_expires_at is not None
        and booking.hold_expires_at <= timezone.now()
    ):

        booking.status = Booking.Status.EXPIRED

        booking.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        # Release seats belonging to the expired hold.
        booking.booking_seats.all().delete()

    return booking
# ============================================================
# EXPIRE SHOWTIME HOLDS
# ============================================================

@transaction.atomic
def expire_holds_for_showtime(showtime):
    """
    Expire all expired holds for a showtime and release
    their temporarily reserved seats.
    """

    now = timezone.now()

    expired_bookings = list(
        Booking.objects.filter(
            showtime=showtime,
            status=Booking.Status.HELD,
            hold_expires_at__lte=now,
        )
    )

    for booking in expired_bookings:

        booking.status = Booking.Status.EXPIRED

        booking.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        booking.booking_seats.all().delete()