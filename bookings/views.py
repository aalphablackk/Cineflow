from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from showtimes.models import Showtime

from .forms import (
    AssignedBookingForm,
    GeneralBookingForm,
)
from .models import Booking
from .services import (
    create_assigned_hold,
    create_general_hold,
    expire_booking,
    get_available_capacity,
    get_available_seat_count,
    get_seat_map,
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

        expire_booking(booking)

        booking.refresh_from_db()


    booking_seats = booking.booking_seats.all()


    return render(
        request,
        "bookings/booking_detail.html",
        {
            "booking": booking,
            "booking_seats": booking_seats,
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