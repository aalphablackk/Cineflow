from datetime import timedelta
import secrets

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from cinemas.models import Seat
from showtimes.models import Showtime

from .models import Booking, BookingSeat, Payment


# ============================================================
# CONFIGURATION
# ============================================================

HOLD_DURATION_MINUTES = 2


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
# INTERNAL BOOKING EXPIRATION HELPER
# ============================================================

def _expire_booking_locked(booking):
    """
    Expire an already-locked HELD booking.

    IMPORTANT:
    This function does not use transaction.atomic itself.

    It is designed to be called from another transaction where
    the booking is already locked.

    This prevents expiration changes from being rolled back when
    the caller needs to raise a ValidationError after the
    transaction has completed.
    """

    if booking.status != Booking.Status.HELD:
        return False

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at > timezone.now()
    ):
        return False

    # --------------------------------------------------------
    # Mark booking expired
    # --------------------------------------------------------

    booking.status = Booking.Status.EXPIRED

    booking.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    # --------------------------------------------------------
    # Mark pending payments as failed
    # --------------------------------------------------------

    Payment.objects.filter(
        booking=booking,
        status=Payment.Status.PENDING,
    ).update(
        status=Payment.Status.FAILED,
        updated_at=timezone.now(),
    )

    # --------------------------------------------------------
    # Release temporarily held seats
    # --------------------------------------------------------

    booking.booking_seats.all().delete()

    return True


# ============================================================
# CONFIRM BOOKING
# ============================================================

# ============================================================
# CONFIRM BOOKING
# ============================================================

def confirm_booking(booking):
    """
    Confirm a held booking.

    If the booking has expired, persist the expiration
    first, then raise ValidationError after the transaction
    has committed.
    """

    booking_expired = False

    with transaction.atomic():

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

        # ----------------------------------------------------
        # 1. Booking must still be held
        # ----------------------------------------------------

        if booking.status != Booking.Status.HELD:
            raise ValidationError(
                "This booking is no longer available for payment."
            )

        # ----------------------------------------------------
        # 2. Check expiration
        # ----------------------------------------------------

        if (
            booking.hold_expires_at is None
            or booking.hold_expires_at <= timezone.now()
        ):

            _expire_booking_locked(
                booking
            )

            booking_expired = True

        else:

            # ------------------------------------------------
            # 3. Confirm booking
            # ------------------------------------------------

            booking.status = Booking.Status.CONFIRMED

            booking.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

    # --------------------------------------------------------
    # IMPORTANT:
    # We are now OUTSIDE the atomic block.
    # The EXPIRED status has already been committed.
    # --------------------------------------------------------

    if booking_expired:
        raise ValidationError(
            "Your booking hold has expired. "
            "Please start a new booking."
        )

    return booking

# ============================================================
# PROCESS SUCCESSFUL PAYMENT
# ============================================================
# ============================================================
# PROCESS SUCCESSFUL PAYMENT
# ============================================================

def process_successful_payment(payment):
    """
    Process a successful payment and confirm its booking.

    Database changes for expired bookings or failed amount
    verification are committed before ValidationError is raised.
    """

    booking_expired = False
    amount_mismatch = False

    with transaction.atomic():

        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "booking",
                "booking__showtime",
            )
            .get(
                pk=payment.pk,
            )
        )

        booking = payment.booking

        # ----------------------------------------------------
        # 1. Payment must still be pending
        # ----------------------------------------------------

        if payment.status != Payment.Status.PENDING:
            raise ValidationError(
                "This payment has already been processed."
            )

        # ----------------------------------------------------
        # 2. Booking must still be held
        # ----------------------------------------------------

        if booking.status != Booking.Status.HELD:
            raise ValidationError(
                "This booking is no longer available for payment."
            )

        # ----------------------------------------------------
        # 3. Check booking hold expiration
        # ----------------------------------------------------

        if (
            booking.hold_expires_at is None
            or booking.hold_expires_at <= timezone.now()
        ):

            _expire_booking_locked(
                booking
            )

            booking_expired = True

        # ----------------------------------------------------
        # 4. Verify payment amount
        # ----------------------------------------------------

        elif payment.amount != booking.total_amount:

            payment.status = Payment.Status.FAILED

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

            amount_mismatch = True

        else:

            # ------------------------------------------------
            # 5. Mark payment successful
            # ------------------------------------------------

            payment.status = Payment.Status.SUCCESSFUL

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

            # ------------------------------------------------
            # 6. Confirm booking
            # ------------------------------------------------

            booking.status = Booking.Status.CONFIRMED
            booking.hold_expires_at = None

            booking.save(
                update_fields=[
                    "status",
                    "hold_expires_at",
                    "updated_at",
                ],
            )

    # --------------------------------------------------------
    # At this point the atomic transaction has successfully
    # committed, so these errors will NOT undo the updates.
    # --------------------------------------------------------

    if booking_expired:
        raise ValidationError(
            "Your booking hold has expired. "
            "Payment cannot be completed."
        )

    if amount_mismatch:
        raise ValidationError(
            "Payment amount verification failed."
        )

    return payment


# ============================================================
# EXPIRE A BOOKING
# ============================================================

@transaction.atomic
def expire_booking(booking):
    """
    Expire a booking whose hold period has ended.

    Any pending payment associated with the booking
    is marked as failed.

    Temporarily held seats are also released.
    """

    with transaction.atomic():

        booking = (
            Booking.objects
            .select_for_update()
            .get(
                pk=booking.pk,
            )
        )

        _expire_booking_locked(
            booking
        )

    return booking


# ============================================================
# EXPIRE SHOWTIME HOLDS
# ============================================================

@transaction.atomic
def expire_holds_for_showtime(showtime):
    """
    Expire all expired holds for a showtime.

    Pending payments are marked as failed and
    temporarily held seats are released.
    """

    now = timezone.now()

    expired_bookings = list(
        Booking.objects
        .select_for_update()
        .filter(
            showtime=showtime,
            status=Booking.Status.HELD,
            hold_expires_at__lte=now,
        )
    )

    for booking in expired_bookings:

        _expire_booking_locked(
            booking
        )