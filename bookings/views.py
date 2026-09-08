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
from .services import cancel_booking
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
    cancel_booking,
    process_successful_payment,
    refund_booking_payment,
    _synchronize_refund_status,
)
from django.views.decorators.http import require_POST
from notifications.services import send_booking_cancellation_email
import hashlib
import hmac
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
@require_POST
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

    print("\n" + "=" * 70)
    print("PAYSTACK CALLBACK REACHED")
    print("REFERENCE:", reference)
    print("GET DATA:", request.GET)
    print("=" * 70)

    # ========================================================
    # CHECK REFERENCE
    # ========================================================

    if not reference:

        print("❌ NO REFERENCE")

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

    print("PAYMENT ID:", payment.id)
    print("PAYMENT REFERENCE:", payment.payment_reference)
    print("PAYMENT STATUS:", payment.status)
    print("PAYMENT AMOUNT:", payment.amount)

    print("BOOKING ID:", booking.id)
    print("BOOKING REFERENCE:", booking.booking_reference)
    print("BOOKING STATUS:", booking.status)
    print("HOLD EXPIRES:", booking.hold_expires_at)

    # ========================================================
    # ALREADY SUCCESSFUL
    # ========================================================

    if payment.status == Payment.Status.SUCCESSFUL:

        print("✅ PAYMENT ALREADY SUCCESSFUL")

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

        print(
            "❌ BOOKING NOT HELD:",
            booking.status,
        )

        messages.error(
            request,
            (
                "This booking is no longer available. "
                f"Current status: {booking.status}"
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

        print("❌ BOOKING HOLD EXPIRED")

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

    print("🔄 VERIFYING PAYMENT WITH PAYSTACK...")

    try:

        transaction_data = verify_transaction(
            payment.payment_reference
        )

    except PaystackError as exc:

        print("❌ PAYSTACK VERIFICATION ERROR:")
        print(exc)

        messages.error(
            request,
            f"Paystack verification failed: {exc}",
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    # ========================================================
    # PRINT PAYSTACK RESPONSE
    # ========================================================

    print("\n" + "=" * 70)
    print("PAYSTACK VERIFICATION RESPONSE")
    print(transaction_data)
    print("=" * 70)

    # ========================================================
    # VERIFY REFERENCE
    # ========================================================

    paystack_reference = transaction_data.get(
        "reference"
    )

    print(
        "REFERENCE CHECK:",
        payment.payment_reference,
        "==",
        paystack_reference,
    )

    if paystack_reference != payment.payment_reference:

        print("❌ REFERENCE MISMATCH")

        messages.error(
            request,
            "Payment reference verification failed.",
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    print("✅ REFERENCE VERIFIED")

    # ========================================================
    # VERIFY CURRENCY
    # ========================================================

    paystack_currency = transaction_data.get(
        "currency"
    )

    print(
        "CURRENCY:",
        paystack_currency,
    )

    if paystack_currency != "NGN":

        print("❌ CURRENCY MISMATCH")

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

    print("✅ CURRENCY VERIFIED")

    # ========================================================
    # VERIFY AMOUNT
    # ========================================================

    expected_amount = int(payment.amount * 100)
    requested_amount = transaction_data.get("requested_amount")

    print(
        f"AMOUNT CHECK: {expected_amount} == {requested_amount}"
    )

    if requested_amount != expected_amount:
        print("❌ AMOUNT MISMATCH")

        messages.error(
            request,
            "Payment amount verification failed."
        )

        return redirect(
            "bookings:checkout",
            booking_id=booking.id,
        )

    print("✅ AMOUNT VERIFIED")

    # ========================================================
    # VERIFY STATUS
    # ========================================================

    paystack_status = transaction_data.get(
        "status"
    )

    print(
        "PAYSTACK STATUS:",
        paystack_status,
    )

    if paystack_status != "success":

        print("❌ PAYMENT NOT SUCCESSFUL")

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

    print("✅ PAYSTACK PAYMENT SUCCESSFUL")

    # ========================================================
    # PROCESS SUCCESSFUL PAYMENT
    # ========================================================

    print(
        "🔄 PROCESSING CINEFLOW PAYMENT..."
    )

    try:

        process_successful_payment(
            payment
        )

    except ValidationError as exc:

        print(
            "❌ CINEFLOW PAYMENT PROCESSING ERROR:"
        )
        print(exc)

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

    print(
        "✅ CINEFLOW PAYMENT PROCESSED SUCCESSFULLY"
    )

    messages.success(
        request,
        "Payment successful! Your booking has been confirmed.",
    )

    return redirect(
        "bookings:booking_detail",
        booking_reference=booking.booking_reference,
    )
# ============================================================
# PAYSTACK WEBHOOK
# ============================================================

@csrf_exempt
def paystack_webhook(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "status": False,
                "message": "Method not allowed.",
            },
            status=405,
        )

    payload = request.body

    signature = request.headers.get(
        "x-paystack-signature"
    )

    if not signature:
        return JsonResponse(
            {
                "status": False,
                "message": "Missing Paystack signature.",
            },
            status=401,
        )

    # --------------------------------------------------------
    # VERIFY PAYSTACK SIGNATURE
    # --------------------------------------------------------

    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected_signature,
    ):
        return JsonResponse(
            {
                "status": False,
                "message": "Invalid Paystack signature.",
            },
            status=401,
        )

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:
        event_data = json.loads(
            payload.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "status": False,
                "message": "Invalid JSON payload.",
            },
            status=400,
        )

    event = event_data.get("event")
    data = event_data.get("data") or {}

    print("\n" + "=" * 70)
    print("PAYSTACK WEBHOOK RECEIVED")
    print("EVENT:", event)
    print("DATA:", data)
    print("=" * 70)

    # --------------------------------------------------------
    # REFUND EVENTS
    # --------------------------------------------------------

    refund_events = {
        "refund.pending",
        "refund.processing",
        "refund.needs-attention",
        "refund.failed",
        "refund.processed",
    }

    # We only process refund events here.
    if event not in refund_events:
        return JsonResponse(
            {
                "status": True,
                "message": "Event received.",
            },
            status=200,
        )

    # --------------------------------------------------------
    # FIND REFUND RECORD
    # --------------------------------------------------------

    refund_id = data.get(
        "refund_reference"
    )

    transaction_reference = data.get(
        "transaction_reference"
    )

    from .models import Refund

    refund = None

    # First try the Paystack refund reference.
    if refund_id:
        refund = (
            Refund.objects
            .select_related(
                "payment",
                "payment__booking",
                "payment__booking__user",
            )
            .filter(
                refund_reference=str(
                    refund_id
                )
            )
            .first()
        )

    # If that fails, try the transaction reference.
    if (
        refund is None
        and transaction_reference
    ):
        refund = (
            Refund.objects
            .select_related(
                "payment",
                "payment__booking",
                "payment__booking__user",
            )
            .filter(
                paystack_transaction=str(
                    transaction_reference
                )
            )
            .first()
        )

    # --------------------------------------------------------
    # UNKNOWN REFUND
    # --------------------------------------------------------

    if refund is None:
        print(
            "⚠️ CineFlow refund record not found."
        )

        # Return 200 so Paystack does not keep
        # retrying a webhook that CineFlow cannot map.
        return JsonResponse(
            {
                "status": True,
                "message": (
                    "Webhook received but "
                    "refund not found."
                ),
            },
            status=200,
        )

    # --------------------------------------------------------
    # SYNCHRONIZE REFUND
    # --------------------------------------------------------

    try:
        refund, status_changed = (
            _synchronize_refund_status(
                refund,
                data,
            )
        )

    except ValidationError as exc:
        print(
            "⚠️ Refund synchronization failed:"
        )
        print(exc)

        return JsonResponse(
            {
                "status": False,
                "message": exc.messages[0],
            },
            status=400,
        )

    # --------------------------------------------------------
    # SEND STATUS EMAIL ONLY ON CHANGE
    # --------------------------------------------------------

    if status_changed:
        try:
            from notifications.services import (
                send_refund_status_email
            )

            send_refund_status_email(
                refund
            )

        except Exception as exc:
            print(
                "❌ Refund status email failed:"
            )
            print(exc)

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print(
        "✅ Refund webhook synchronized:"
    )
    print(
        f"   Status: {refund.status}"
    )

    return JsonResponse(
        {
            "status": True,
            "message": (
                "Webhook processed successfully."
            ),
        },
        status=200,
    )
# ============================================================
# CANCEL BOOKING
# ============================================================

@login_required
def cancel_booking_view(request, booking_reference):
    """
    Cancel a customer's confirmed booking and
    initiate the associated Paystack refund.
    """

    if request.method != "POST":
        return redirect(
            "bookings:booking_detail",
            booking_reference=booking_reference,
        )

    booking = get_object_or_404(
        Booking,
        booking_reference=booking_reference,
        user=request.user,
    )

    # ========================================================
    # 1. CANCEL BOOKING
    # ========================================================

    try:

        booking = cancel_booking(
            booking
        )

    except ValidationError as exc:

        messages.error(
            request,
            exc.messages[0],
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    # ========================================================
    # 2. INITIATE REFUND
    # ========================================================

    try:

        payment, refund = refund_booking_payment(
            booking
        )

    except ValidationError as exc:

        # ----------------------------------------------------
        # IMPORTANT:
        # The booking is already cancelled.
        #
        # A refund failure should NOT undo the cancellation.
        # ----------------------------------------------------

        messages.warning(
            request,
            (
                "Your booking has been cancelled, but we "
                "could not initiate the refund automatically. "
                "Our team will review the refund."
            ),
        )

        return redirect(
            "bookings:booking_detail",
            booking_reference=booking.booking_reference,
        )

    try:
        send_booking_cancellation_email(
            booking,
            refund,
        )
    except Exception as exc:
        print(
            f"CineFlow cancellation email failed: {exc}"
        )
    # ========================================================
    # 3. REFUND RESULT
    # ========================================================

    if refund.status == "processed":

        messages.success(
            request,
            (
                "Your booking has been cancelled and "
                "your payment has been refunded successfully."
            ),
        )

    elif refund.status in [
        "pending",
        "processing",
    ]:

        messages.success(
            request,
            (
                "Your booking has been cancelled. "
                "Your refund has been initiated and is "
                "currently being processed."
            ),
        )

    elif refund.status == "failed":

        messages.warning(
            request,
            (
                "Your booking has been cancelled, but the "
                "refund could not be completed automatically. "
                "Our team will review it."
            ),
        )

    else:

        messages.success(
            request,
            "Your booking has been cancelled successfully.",
        )

    # ========================================================
    # 4. REDIRECT
    # ========================================================

    return redirect(
        "bookings:booking_detail",
        booking_reference=booking.booking_reference,
    )