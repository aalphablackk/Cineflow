from datetime import timedelta, datetime
import secrets

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from cinemas.models import Seat
from showtimes.models import Showtime
from tickets.models import Ticket

from .models import (
    Booking,
    BookingSeat,
    Payment,
    Refund,
    SeatReservation,
)

from .paystack import (
    PaystackError,
    create_refund,
    fetch_refund,
)

from tickets.services import create_ticket
from notifications.services import send_ticket_confirmation_email


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

    SeatReservation represents the current active
    reservation of a seat.

    Historical BookingSeat records are intentionally
    ignored here so cancelled and expired bookings
    can retain their history.
    """

    occupied_seat_ids = (
        SeatReservation.objects
        .filter(
            showtime=showtime,
            booking__status__in=[
                Booking.Status.HELD,
                Booking.Status.CONFIRMED,
            ],
        )
        .values_list(
            "seat_id",
            flat=True,
        )
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

    SeatReservation determines current occupancy.
    """

    occupied_seat_ids = set(
        SeatReservation.objects
        .filter(
            showtime=showtime,
            booking__status__in=[
                Booking.Status.HELD,
                Booking.Status.CONFIRMED,
            ],
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

    BookingSeat stores the historical booking-seat record.

    SeatReservation stores the current active reservation.

    This allows cancelled/expired bookings to retain
    their original seat history while releasing the
    seats for future customers.
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

    if not showtime.is_bookable:
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
    # 4. Convert Seat objects to unique IDs
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
    # 8. Check active seat reservations
    # --------------------------------------------------------

    occupied_seat_ids = set(
        SeatReservation.objects
        .filter(
            showtime=showtime,
            seat_id__in=seat_ids,
            booking__status__in=[
                Booking.Status.HELD,
                Booking.Status.CONFIRMED,
            ],
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
    # 11. Create historical BookingSeat records
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

    # --------------------------------------------------------
    # 12. Create active SeatReservation records
    # --------------------------------------------------------

    reservations = [
        SeatReservation(
            booking=booking,
            showtime=showtime,
            seat=seat,
        )
        for seat in seats
    ]

    SeatReservation.objects.bulk_create(
        reservations
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

    if not showtime.is_bookable:
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

    Historical BookingSeat records are preserved.

    Active SeatReservation records are removed so the
    seats become available again.
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
    # Release active seat reservations
    # --------------------------------------------------------

    SeatReservation.objects.filter(
        booking=booking,
    ).delete()

    # --------------------------------------------------------
    # IMPORTANT:
    # BookingSeat records are NOT deleted.
    #
    # They remain as historical records of what the
    # customer originally selected.
    # --------------------------------------------------------

    return True


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
    # Important:
    # We are now outside the atomic block.
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

            # ------------------------------------------------
            # 7. Create digital ticket
            # ------------------------------------------------

            ticket = create_ticket(
                booking
            )

            transaction.on_commit(
                lambda ticket=ticket:
                send_ticket_confirmation_email(
                    ticket
                )
            )

    # --------------------------------------------------------
    # At this point the transaction has committed.
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

    Pending payments are marked as failed.

    Active seat reservations are released.

    Historical BookingSeat records are preserved.
    """

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

    Pending payments are marked as failed.

    Active seat reservations are released.

    Historical BookingSeat records are preserved.
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


# ============================================================
# CANCEL BOOKING
# ============================================================

@transaction.atomic
def cancel_booking(booking):
    """
    Cancel a confirmed booking.

    This function:

    - Locks the booking inside a database transaction
    - Validates that it can be cancelled
    - Prevents cancellation after the showtime has started
    - Locks and invalidates the digital ticket
    - Releases the active seat reservations
    - Changes the booking status to CANCELLED

    Historical BookingSeat records are preserved.

    Payment is NOT refunded here.
    The Paystack refund is handled separately.
    """

    # --------------------------------------------------------
    # 1. Lock the booking
    # --------------------------------------------------------

    booking = (
        Booking.objects
        .select_for_update()
        .select_related(
            "user",
            "showtime",
            "showtime__movie",
            "showtime__screen",
            "showtime__screen__cinema",
        )
        .get(
            pk=booking.pk,
        )
    )

    # --------------------------------------------------------
    # 2. Booking must be confirmed
    # --------------------------------------------------------

    if booking.status != Booking.Status.CONFIRMED:
        raise ValidationError(
            "Only confirmed bookings can be cancelled."
        )

    # --------------------------------------------------------
    # 3. Showtime must not have started
    # --------------------------------------------------------

    showtime = booking.showtime

    showtime_start = timezone.make_aware(
        datetime.combine(
            showtime.show_date,
            showtime.start_time,
        )
    )

    if showtime_start <= timezone.now():
        raise ValidationError(
            "This booking can no longer be cancelled because "
            "the showtime has already started."
        )

    # --------------------------------------------------------
    # 4. Lock and invalidate digital ticket
    # --------------------------------------------------------

    try:
        ticket = (
            Ticket.objects
            .select_for_update()
            .get(
                booking=booking,
            )
        )

    except Ticket.DoesNotExist:
        ticket = None

    if ticket:

        # A ticket that has already been used cannot be cancelled.
        if ticket.used_at is not None:
            raise ValidationError(
                "This ticket has already been used and "
                "cannot be cancelled."
            )

        ticket.is_valid = False

        ticket.save(
            update_fields=[
                "is_valid",
                "updated_at",
            ],
        )

    # --------------------------------------------------------
    # 5. Release active seat reservations
    # --------------------------------------------------------

    SeatReservation.objects.filter(
        booking=booking,
    ).delete()

    # --------------------------------------------------------
    # 6. Cancel booking
    # --------------------------------------------------------

    booking.status = Booking.Status.CANCELLED
    booking.hold_expires_at = None

    booking.save(
        update_fields=[
            "status",
            "hold_expires_at",
            "updated_at",
        ],
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # BookingSeat records are intentionally preserved.
    #
    # BookingSeat = historical record
    # SeatReservation = active seat reservation
    # --------------------------------------------------------

    return booking
# ============================================================
# REFUND STATUS HELPERS
# ============================================================

def _get_refund_status_order(status):
    """
    Return a comparable order for refund statuses.

    Prevents older/out-of-order webhook events from
    moving a refund backwards.
    """

    status_order = {
        Refund.Status.PENDING: 1,
        Refund.Status.PROCESSING: 2,
        Refund.Status.NEEDS_ATTENTION: 2,
        Refund.Status.FAILED: 3,
        Refund.Status.PROCESSED: 4,
    }

    return status_order.get(status, 0)


def _synchronize_refund_status(
    refund_record,
    refund_data,
):
    """
    Apply a Paystack refund status safely.

    Used by both:
    - Paystack webhook
    - Staff manual refund-status check
    """

    if refund_record is None:
        raise ValidationError(
            "Refund record was not found."
        )

    refund_status = refund_data.get("status")

    valid_statuses = [
        Refund.Status.PENDING,
        Refund.Status.PROCESSING,
        Refund.Status.NEEDS_ATTENTION,
        Refund.Status.PROCESSED,
        Refund.Status.FAILED,
    ]

    if refund_status not in valid_statuses:
        raise ValidationError(
            "Paystack returned an unknown refund status."
        )

    previous_status = refund_record.status

    current_order = _get_refund_status_order(
        previous_status
    )

    incoming_order = _get_refund_status_order(
        refund_status
    )

    # Never allow processed refunds to roll backwards.
    if (
        previous_status == Refund.Status.PROCESSED
        and refund_status != Refund.Status.PROCESSED
    ):
        return refund_record, False

    # Ignore older/out-of-order statuses.
    if incoming_order < current_order:
        return refund_record, False

    refund_record.status = refund_status

    # --------------------------------------------------------
    # Refund reference
    # --------------------------------------------------------

    refund_id = (
        refund_data.get("id")
        or refund_data.get("refund_reference")
    )

    if refund_id is not None:
        refund_record.refund_reference = str(
            refund_id
        )

    # --------------------------------------------------------
    # Transaction reference
    # --------------------------------------------------------

    transaction_reference = (
        refund_data.get("transaction_reference")
        or refund_data.get("transaction")
    )

    if isinstance(transaction_reference, dict):
        transaction_reference = (
            transaction_reference.get("reference")
            or transaction_reference.get("id")
        )

    if transaction_reference is not None:
        refund_record.paystack_transaction = str(
            transaction_reference
        )

    # --------------------------------------------------------
    # Expected date
    # --------------------------------------------------------

    expected_at = refund_data.get("expected_at")

    if expected_at:
        from django.utils.dateparse import parse_datetime

        parsed_expected_at = parse_datetime(
            expected_at
        )

        if parsed_expected_at:
            refund_record.expected_at = parsed_expected_at

    # --------------------------------------------------------
    # Processed
    # --------------------------------------------------------

    if refund_status == Refund.Status.PROCESSED:

        if refund_record.processed_at is None:
            refund_record.processed_at = timezone.now()

        payment = refund_record.payment

        if payment.status != Payment.Status.REFUNDED:
            payment.status = Payment.Status.REFUNDED

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

    # --------------------------------------------------------
    # Failed
    # --------------------------------------------------------

    elif refund_status == Refund.Status.FAILED:

        refund_record.failure_reason = (
            refund_data.get("failure_reason")
            or refund_data.get("message")
            or "Paystack refund failed."
        )

    refund_record.save(
        update_fields=[
            "status",
            "refund_reference",
            "paystack_transaction",
            "expected_at",
            "processed_at",
            "failure_reason",
            "updated_at",
        ],
    )

    return (
        refund_record,
        previous_status != refund_status,
    )
# ============================================================
# REFUND BOOKING PAYMENT
# ============================================================

def refund_booking_payment(booking):
    """
    Request a refund for the successful Paystack payment
    associated with a cancelled booking.

    The booking must already be cancelled.

    Database locking is performed only inside short
    transactions. The Paystack API request is intentionally
    performed outside a database transaction.

    Refund status is stored separately from the Payment model
    because Paystack refunds can remain pending or processing
    before they are finally processed.
    """

    # ========================================================
    # 1. LOCK AND PREPARE REFUND RECORD
    # ========================================================

    with transaction.atomic():

        booking = (
            Booking.objects
            .select_for_update()
            .get(
                pk=booking.pk,
            )
        )

        # ----------------------------------------------------
        # Booking must be cancelled
        # ----------------------------------------------------

        if booking.status != Booking.Status.CANCELLED:
            raise ValidationError(
                "Only cancelled bookings can be refunded."
            )

        # ----------------------------------------------------
        # Find successful payment
        # ----------------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .filter(
                booking=booking,
                status=Payment.Status.SUCCESSFUL,
            )
            .order_by("-created_at")
            .first()
        )

        if payment is None:
            raise ValidationError(
                "No successful payment was found for this booking."
            )

        # ----------------------------------------------------
        # Only Paystack payments can be refunded
        # ----------------------------------------------------

        if payment.provider != Payment.Provider.PAYSTACK:
            raise ValidationError(
                "This booking does not have a Paystack payment."
            )

        # ----------------------------------------------------
        # Check existing refund
        # ----------------------------------------------------

        refund_record = (
            Refund.objects
            .select_for_update()
            .filter(
                payment=payment,
            )
            .first()
        )

        # ----------------------------------------------------
        # Existing refund
        # ----------------------------------------------------

        if refund_record:

            if refund_record.status in [
                Refund.Status.PENDING,
                Refund.Status.PROCESSING,
                Refund.Status.PROCESSED,
            ]:
                return payment, refund_record

        # ----------------------------------------------------
        # Create refund record if necessary
        # ----------------------------------------------------

        if refund_record is None:

            refund_record = Refund.objects.create(
                payment=payment,
                amount=payment.amount,
                status=Refund.Status.PENDING,
                reason=(
                    f"Refund for cancelled CineFlow booking "
                    f"{booking.booking_reference}."
                ),
                customer_note=(
                    "Refund for cancelled CineFlow booking "
                    f"{booking.booking_reference}."
                ),
                merchant_note=(
                    f"CineFlow booking cancellation: "
                    f"{booking.booking_reference}"
                ),
                paystack_transaction=(
                    payment.payment_reference
                ),
            )

        # ----------------------------------------------------
        # Save IDs we need after leaving transaction
        # ----------------------------------------------------

        payment_id = payment.id
        payment_reference = payment.payment_reference
        payment_amount = payment.amount
        booking_reference = booking.booking_reference
        refund_id = refund_record.id

    # ========================================================
    # IMPORTANT:
    #
    # Database transaction has now committed.
    #
    # Paystack API is called OUTSIDE the transaction.
    # ========================================================

    try:

        refund_data = create_refund(
            transaction=payment_reference,
            amount=payment_amount,
            customer_note=(
                "Refund for cancelled CineFlow booking "
                f"{booking_reference}."
            ),
            merchant_note=(
                f"CineFlow booking cancellation: "
                f"{booking_reference}"
            ),
        )

    except PaystackError as exc:
        print("\n" + "=" * 70)
        print("❌ PAYSTACK REFUND ERROR")
        print("ERROR:", exc)
        print("=" * 70)

        # ----------------------------------------------------
        # Save Paystack failure
        # ----------------------------------------------------

        with transaction.atomic():

            refund_record = (
                Refund.objects
                .select_for_update()
                .get(
                    pk=refund_id,
                )
            )

            refund_record.status = Refund.Status.FAILED
            refund_record.failure_reason = str(exc)

            refund_record.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "updated_at",
                ],
            )

        raise ValidationError(
            str(exc)
        )

    # ========================================================
    # 2. SAVE PAYSTACK REFUND RESULT
    # ========================================================

    with transaction.atomic():

        refund_record = (
            Refund.objects
            .select_for_update()
            .get(
                pk=refund_id,
            )
        )

        payment = (
            Payment.objects
            .select_for_update()
            .get(
                pk=payment_id,
            )
        )

        # ----------------------------------------------------
        # Get Paystack refund status
        # ----------------------------------------------------

        refund_status = refund_data.get(
            "status"
        )

        valid_statuses = [
            Refund.Status.PENDING,
            Refund.Status.PROCESSING,
            Refund.Status.NEEDS_ATTENTION,
            Refund.Status.PROCESSED,
            Refund.Status.FAILED,
        ]

        if refund_status not in valid_statuses:
            refund_status = Refund.Status.PENDING

        # --------------------------------------------------------
        # 5. Get Paystack refund status
        # --------------------------------------------------------

        refund_status = refund_data.get(
            "status"
        )

        valid_statuses = [
            Refund.Status.PENDING,
            Refund.Status.PROCESSING,
            Refund.Status.NEEDS_ATTENTION,
            Refund.Status.PROCESSED,
            Refund.Status.FAILED,
        ]

        if refund_status not in valid_statuses:
            refund_status = Refund.Status.PENDING

        previous_status = refund_record.status
        status_changed = previous_status != refund_status

        refund_record.status = refund_status

        # refund_record.status = refund_status

        # ----------------------------------------------------
        # Refund reference
        # ----------------------------------------------------

        refund_id_from_paystack = refund_data.get(
            "refund_id"
        )

        if refund_id_from_paystack is not None:

            refund_record.refund_reference = str(
                refund_id_from_paystack
            )

        # ----------------------------------------------------
        # Paystack transaction
        # ----------------------------------------------------
        print("\n" + "=" * 70)
        print("PAYSTACK REFUND DATA")
        print(refund_data)
        print("TRANSACTION:", refund_data.get("transaction"))
        print("TRANSACTION TYPE:", type(refund_data.get("transaction")))
        print("=" * 70)
        paystack_transaction = refund_data.get("transaction")

        if isinstance(paystack_transaction, dict):
            transaction_reference = paystack_transaction.get("reference")

            if transaction_reference:
                refund_record.paystack_transaction = str(transaction_reference)

        elif paystack_transaction is not None:
            refund_record.paystack_transaction = str(paystack_transaction)

        # ----------------------------------------------------
        # Amount
        # ----------------------------------------------------

        refund_record.amount = payment.amount

        # ----------------------------------------------------
        # Customer note
        # ----------------------------------------------------

        customer_note = refund_data.get(
            "customer_note"
        )

        if customer_note:
            refund_record.customer_note = customer_note

        # ----------------------------------------------------
        # Merchant note
        # ----------------------------------------------------

        merchant_note = refund_data.get(
            "merchant_note"
        )

        if merchant_note:
            refund_record.merchant_note = merchant_note

        # ----------------------------------------------------
        # Expected refund date
        # ----------------------------------------------------

        expected_at = refund_data.get(
            "expected_at"
        )

        if expected_at:

            from django.utils.dateparse import parse_datetime

            parsed_expected_at = parse_datetime(
                expected_at
            )

            if parsed_expected_at:
                refund_record.expected_at = (
                    parsed_expected_at
                )

        # ----------------------------------------------------
        # Refund processed immediately
        # ----------------------------------------------------

        if refund_record.status == Refund.Status.PROCESSED:

            refund_record.processed_at = timezone.now()

            payment.status = Payment.Status.REFUNDED

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

        # ----------------------------------------------------
        # Refund failed
        # ----------------------------------------------------

        elif refund_record.status == Refund.Status.FAILED:

            raw_response = refund_data.get(
                "raw",
                {},
            )

            refund_record.failure_reason = (
                raw_response.get(
                    "message",
                    "Paystack refund failed.",
                )
            )

        # ----------------------------------------------------
        # Save refund
        # ----------------------------------------------------

        refund_record.save(
            update_fields=[
                "status",
                "refund_reference",
                "amount",
                "paystack_transaction",
                "customer_note",
                "merchant_note",
                "expected_at",
                "processed_at",
                "failure_reason",
                "updated_at",
            ],
        )

    return payment, refund_record
# ============================================================
# CHECK REFUND STATUS
# ============================================================

def update_refund_status(refund_record):
    """
    Fetch the current refund status from Paystack
    and synchronize the CineFlow Refund and Payment records.

    A refund-status email is sent only when the status
    actually changes.
    """

    from notifications.services import (
        send_refund_status_email
    )

    if refund_record is None:
        raise ValidationError(
            "Refund record was not found."
        )

    if refund_record.status == Refund.Status.PROCESSED:
        return refund_record

    reference = refund_record.refund_reference

    if not reference:
        raise ValidationError(
            "No Paystack refund ID is available."
        )

    try:
        refund_data = fetch_refund(
            reference
        )

    except PaystackError as exc:
        raise ValidationError(
            str(exc)
        )

    refund_record, status_changed = (
        _synchronize_refund_status(
            refund_record,
            refund_data,
        )
    )

    if status_changed:
        try:
            send_refund_status_email(
                refund_record
            )

        except Exception as exc:
            print(
                f"CineFlow refund status email failed: {exc}"
            )

    return refund_record