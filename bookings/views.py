from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.utils import timezone

import uuid

from showtimes.models import Showtime

from .forms import (
    AssignedBookingForm,
    GeneralBookingForm,
)
from .models import Booking, Payment
from .paystack import (
    PaystackError,
    initialize_transaction,
    verify_transaction,
)
from .services import (
    create_assigned_hold,
    create_general_hold,
    expire_booking,
    generate_booking_reference,
    get_available_capacity,
    get_available_seat_count,
    get_seat_map,
    process_successful_payment,
)


# ============================================================
# CREATE BOOKING
# ============================================================

@login_required
def create_booking(request, showtime_id):

    showtime = get_object_or_404(
        Showtime.objects.select_related(
            "movie",
            "screen",
            "screen__cinema",
        ),
        id=showtime_id,
    )

    # ========================================================
    # CHECK SHOWTIME STATUS
    # ========================================================

    if showtime.status != Showtime.Status.SCHEDULED:

        messages.error(
            request,
            "This showtime is no longer available for booking.",
        )

        return redirect(
            "movies:movie_detail",
            slug=showtime.movie.slug,
        )

    # ========================================================
    # AVAILABILITY
    # ========================================================

    available_capacity = get_available_capacity(
        showtime
    )

    available_seat_count = (
        get_available_seat_count(showtime)
        if showtime.booking_mode
        == Showtime.BookingMode.ASSIGNED
        else 0
    )

    seat_map = (
        get_seat_map(showtime)
        if showtime.booking_mode
        == Showtime.BookingMode.ASSIGNED
        else []
    )

    # ========================================================
    # SELECT THE CORRECT FORM
    # ========================================================

    if showtime.booking_mode == Showtime.BookingMode.ASSIGNED:

        if request.method == "POST":

            form = AssignedBookingForm(
                request.POST,
                showtime=showtime,
            )

        else:

            form = AssignedBookingForm(
                showtime=showtime,
            )

    else:

        if request.method == "POST":

            form = GeneralBookingForm(
                request.POST,
                available_capacity=available_capacity,
            )

        else:

            form = GeneralBookingForm(
                available_capacity=available_capacity,
            )

    # ========================================================
    # HANDLE SUBMISSION
    # ========================================================

    if request.method == "POST":

        if form.is_valid():

            try:

                # ==================================================
                # ASSIGNED SEATING
                # ==================================================

                if (
                    showtime.booking_mode
                    == Showtime.BookingMode.ASSIGNED
                ):

                    seat_ids = form.cleaned_data[
                        "seat_ids"
                    ]

                    booking = create_assigned_hold(
                        user=request.user,
                        showtime=showtime,
                        seat_ids=seat_ids,
                    )

                # ==================================================
                # GENERAL ADMISSION
                # ==================================================

                else:

                    ticket_quantity = (
                        form.cleaned_data[
                            "ticket_quantity"
                        ]
                    )

                    booking = create_general_hold(
                        user=request.user,
                        showtime=showtime,
                        ticket_quantity=ticket_quantity,
                    )

                # ==================================================
                # GO TO CHECKOUT
                # ==================================================

                return redirect(
                    "bookings:checkout",
                    booking_id=booking.id,
                )

            except ValidationError as error:

                form.add_error(
                    None,
                    error.message,
                )

    # ========================================================
    # RENDER BOOKING PAGE
    # ========================================================

    return render(
        request,
        "bookings/create_booking.html",
        {
            "showtime": showtime,
            "form": form,
            "available_capacity": available_capacity,
            "available_seat_count": available_seat_count,
            "seat_map": seat_map,
        },
    )


# ============================================================
# BOOKING DETAIL
# ============================================================

@login_required
def booking_detail(
    request,
    booking_reference,
):

    booking = get_object_or_404(
        Booking.objects.select_related(
            "showtime",
            "showtime__movie",
            "showtime__screen",
            "showtime__screen__cinema",
        ).prefetch_related(
            "booking_seats",
            "booking_seats__seat",
            "payments",
        ),
        booking_reference=booking_reference,
        user=request.user,
    )

    # ========================================================
    # CHECK HOLD EXPIRATION
    # ========================================================

    if (
        booking.status == Booking.Status.HELD
        and (
            booking.hold_expires_at is None
            or booking.hold_expires_at <= timezone.now()
        )
    ):

        expire_booking(
            booking
        )

        booking.refresh_from_db()

    # ========================================================
    # GET LATEST PAYMENT
    # ========================================================

    payment = (
        booking.payments
        .order_by("-created_at")
        .first()
    )

    booking_seats = booking.booking_seats.all()

    return render(
        request,
        "bookings/booking_detail.html",
        {
            "booking": booking,
            "booking_seats": booking_seats,
            "payment": payment,
        },
    )


# ============================================================
# CHECKOUT
# ============================================================

@login_required
def checkout(
    request,
    booking_id,
):

    booking = get_object_or_404(
        Booking.objects.select_related(
            "showtime",
            "showtime__movie",
            "showtime__screen",
            "showtime__screen__cinema",
        ).prefetch_related(
            "booking_seats",
            "booking_seats__seat",
        ),
        id=booking_id,
        user=request.user,
    )

    # ========================================================
    # CHECK BOOKING STATUS
    # ========================================================

    if booking.status != Booking.Status.HELD:

        messages.error(
            request,
            "This booking is no longer available.",
        )

        return redirect(
            "movies:movie_detail",
            slug=booking.showtime.movie.slug,
        )

    # ========================================================
    # CHECK HOLD EXPIRATION
    # ========================================================

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at <= timezone.now()
    ):

        expire_booking(
            booking
        )

        messages.error(
            request,
            "Your booking hold has expired. "
            "Please start a new booking.",
        )

        return redirect(
            "movies:movie_detail",
            slug=booking.showtime.movie.slug,
        )

    # ========================================================
    # RENDER CHECKOUT
    # ========================================================

    return render(
        request,
        "bookings/checkout.html",
        {
            "booking": booking,
            "booking_seats": booking.booking_seats.all(),
        },
    )


# ============================================================
# MY BOOKINGS
# ============================================================

@login_required
def my_bookings(request):

    bookings = (
        Booking.objects
        .filter(
            user=request.user,
        )
        .select_related(
            "showtime",
            "showtime__movie",
            "showtime__screen",
            "showtime__screen__cinema",
        )
        .prefetch_related(
            "booking_seats",
            "booking_seats__seat",
        )
        .order_by(
            "-created_at",
        )
    )

    return render(
        request,
        "bookings/my_bookings.html",
        {
            "bookings": bookings,
        },
    )


# ============================================================
# PAYMENT INITIALIZATION
# ============================================================

@login_required
def initialize_payment(request, booking_id):

    booking = get_object_or_404(
        Booking.objects.select_related(
            "showtime",
            "showtime__movie",
        ),
        pk=booking_id,
        user=request.user,
    )

    # ========================================================
    # CHECK BOOKING STATUS
    # ========================================================

    if booking.status != Booking.Status.HELD:

        messages.error(
            request,
            "This booking is no longer available for payment.",
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # CHECK HOLD EXPIRATION
    # ========================================================

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at <= timezone.now()
    ):

        expire_booking(booking)

        messages.error(
            request,
            "Your booking hold has expired. "
            "Please start a new booking.",
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # GET EXISTING PENDING PAYMENT
    # ========================================================

    payment = (
        Payment.objects
        .filter(
            booking=booking,
            status=Payment.Status.PENDING,
        )
        .order_by("-created_at")
        .first()
    )

    # ========================================================
    # CREATE PAYMENT
    # ========================================================

    if payment is None:

        payment = Payment.objects.create(
            booking=booking,
            payment_reference=(
                f"PAY-{uuid.uuid4().hex.upper()}"
            ),
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.PAYSTACK,
        )

    # ========================================================
    # PAYSTACK CALLBACK URL
    # ========================================================

    callback_url = request.build_absolute_uri(
        reverse(
            "bookings:paystack_callback"
        )
    )

    # ========================================================
    # INITIALIZE PAYSTACK TRANSACTION
    # ========================================================

    try:

        paystack_data = initialize_transaction(
            email=request.user.email,
            amount=payment.amount,
            reference=payment.payment_reference,
            callback_url=callback_url,
            metadata={
                "booking_id": str(booking.id),
                "booking_reference": (
                    booking.booking_reference
                ),
                "payment_id": str(payment.id),
            },
        )

    except PaystackError as exc:

        messages.error(
            request,
            str(exc),
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # REDIRECT TO PAYSTACK
    # ========================================================

    return redirect(
        paystack_data["authorization_url"]
    )


# ============================================================
# TEST PAYMENT
# ============================================================

@login_required
def test_payment(
    request,
    payment_reference,
):

    payment = get_object_or_404(
        Payment.objects.select_related(
            "booking",
            "booking__showtime",
            "booking__showtime__movie",
        ),
        payment_reference=payment_reference,
        booking__user=request.user,
    )

    # ========================================================
    # CHECK PAYMENT STATUS
    # ========================================================

    if payment.status != Payment.Status.PENDING:

        messages.info(
            request,
            "This payment has already been processed.",
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=(
                payment.booking.booking_reference
            ),
        )

    # ========================================================
    # CHECK BOOKING
    # ========================================================

    booking = payment.booking

    if booking.status != Booking.Status.HELD:

        messages.error(
            request,
            "This booking is no longer available.",
        )

        return redirect(
            "bookings:my_bookings",
        )

    # ========================================================
    # CHECK HOLD EXPIRATION
    # ========================================================

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at <= timezone.now()
    ):

        expire_booking(booking)

        messages.error(
            request,
            "Your booking hold has expired.",
        )

        return redirect(
            "movies:movie_detail",
            slug=booking.showtime.movie.slug,
        )

    return render(
        request,
        "bookings/test_payment.html",
        {
            "payment": payment,
            "booking": booking,
        },
    )


# ============================================================
# SIMULATE SUCCESSFUL PAYMENT
# ============================================================

@login_required
@transaction.atomic
def simulate_successful_payment(
    request,
    payment_reference,
):

    if request.method != "POST":

        return redirect(
            "bookings:test_payment",
            payment_reference=payment_reference,
        )

    payment = get_object_or_404(
        Payment.objects.select_related(
            "booking",
            "booking__showtime",
            "booking__showtime__movie",
        ),
        payment_reference=payment_reference,
        booking__user=request.user,
    )

    booking = payment.booking

    try:

        process_successful_payment(
            payment
        )

    except ValidationError as error:

        messages.error(
            request,
            error.message,
        )

        booking.refresh_from_db()

        if booking.status == Booking.Status.EXPIRED:

            return redirect(
                "movies:movie_detail",
                slug=booking.showtime.movie.slug,
            )

        return redirect(
            "bookings:test_payment",
            payment_reference=payment.payment_reference,
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    messages.success(
        request,
        "Payment successful! Your booking has been confirmed.",
    )

    return redirect(
        "bookings:booking_detail",
        booking_reference=booking.booking_reference,
    )


# ============================================================
# SIMULATE FAILED PAYMENT
# ============================================================

@login_required
@transaction.atomic
def simulate_failed_payment(
    request,
    payment_reference,
):

    if request.method != "POST":

        return redirect(
            "bookings:test_payment",
            payment_reference=payment_reference,
        )

    payment = get_object_or_404(
        Payment.objects.select_for_update().select_related(
            "booking",
            "booking__showtime",
            "booking__showtime__movie",
        ),
        payment_reference=payment_reference,
        booking__user=request.user,
    )

    booking = payment.booking

    # ========================================================
    # PAYMENT ALREADY PROCESSED
    # ========================================================

    if payment.status != Payment.Status.PENDING:

        messages.info(
            request,
            "This payment has already been processed.",
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # CHECK BOOKING
    # ========================================================

    if booking.status != Booking.Status.HELD:

        payment.status = Payment.Status.CANCELLED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.error(
            request,
            "This booking is no longer available.",
        )

        return redirect(
            "bookings:my_bookings",
        )

    # ========================================================
    # CHECK HOLD EXPIRATION
    # ========================================================

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at <= timezone.now()
    ):

        expire_booking(booking)

        messages.error(
            request,
            "Your booking hold has expired.",
        )

        return redirect(
            "movies:movie_detail",
            slug=booking.showtime.movie.slug,
        )

    # ========================================================
    # MARK PAYMENT FAILED
    # ========================================================

    payment.status = Payment.Status.FAILED

    payment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.warning(
        request,
        "Payment failed. Your booking has not been confirmed.",
    )

    return redirect(
        "bookings:test_payment",
        payment_reference=payment.payment_reference,
    )


# ============================================================
# PAYSTACK CALLBACK
# ============================================================

@login_required
def paystack_callback(request):

    reference = request.GET.get("reference")

    # ========================================================
    # CHECK REFERENCE
    # ========================================================

    if not reference:

        messages.error(
            request,
            "Paystack returned without a payment reference.",
        )

        return redirect(
            "bookings:my_bookings"
        )

    # ========================================================
    # FIND PAYMENT
    # ========================================================

    payment = get_object_or_404(
        Payment.objects.select_related(
            "booking",
            "booking__showtime",
            "booking__showtime__movie",
        ),
        payment_reference=reference,
        booking__user=request.user,
    )

    booking = payment.booking

    # ========================================================
    # ALREADY SUCCESSFUL
    # ========================================================

    if payment.status == Payment.Status.SUCCESSFUL:

        messages.success(
            request,
            "This payment has already been confirmed.",
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # CHECK BOOKING STATUS
    # ========================================================

    if booking.status != Booking.Status.HELD:

        messages.error(
            request,
            (
                "This booking is no longer available. "
                f"Current booking status: {booking.status}"
            ),
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # CHECK HOLD EXPIRATION
    # ========================================================

    if (
        booking.hold_expires_at is None
        or booking.hold_expires_at <= timezone.now()
    ):

        expire_booking(booking)

        messages.error(
            request,
            "Your CineFlow booking hold has expired.",
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # VERIFY WITH PAYSTACK
    # ========================================================

    try:

        transaction_data = verify_transaction(
            payment.payment_reference
        )

    except PaystackError as exc:

        messages.error(
            request,
            f"Paystack verification failed: {exc}",
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # VERIFY REFERENCE
    # ========================================================

    paystack_reference = transaction_data.get(
        "reference"
    )

    if paystack_reference != payment.payment_reference:

        messages.error(
            request,
            (
                "Payment reference mismatch. "
                f"CineFlow: {payment.payment_reference} | "
                f"Paystack: {paystack_reference}"
            ),
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # VERIFY CURRENCY
    # ========================================================

    paystack_currency = transaction_data.get(
        "currency"
    )

    if paystack_currency != "NGN":

        messages.error(
            request,
            (
                "Payment currency verification failed. "
                f"Expected NGN, received {paystack_currency}."
            ),
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # VERIFY AMOUNT
    # ========================================================

    expected_amount = int(
        payment.amount * 100
    )

    paystack_amount = transaction_data.get(
        "amount"
    )

    if paystack_amount != expected_amount:

        messages.error(
            request,
            (
                "Payment amount verification failed. "
                f"Expected {expected_amount} kobo, "
                f"received {paystack_amount} kobo."
            ),
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # VERIFY PAYMENT STATUS
    # ========================================================

    paystack_status = transaction_data.get(
        "status"
    )

    if paystack_status != "success":

        messages.error(
            request,
            (
                "Paystack did not report a successful payment. "
                f"Current status: {paystack_status}"
            ),
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # PROCESS SUCCESSFUL PAYMENT
    # ========================================================

    try:

        process_successful_payment(
            payment
        )

    except ValidationError as exc:

        messages.error(
            request,
            str(exc),
        )

        booking.refresh_from_db()

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    messages.success(
        request,
        "Payment successful! Your booking has been confirmed.",
    )

    return redirect(
        "bookings:booking_detail",
        booking_reference=booking.booking_reference,
    )