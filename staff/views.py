from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import ProtectedError, Q, Prefetch, Count
from support.forms import SupportReplyForm
from django.contrib.auth.models import User

from .decorators import staff_required

from movies.models import Movie
from movies.forms import StaffMovieForm
from cinemas.models import Cinema,Screen,Seat
from cinemas.forms import CinemaForm,ScreenForm,SeatForm,SeatGenerationForm
from bookings.models import Booking
from datetime import datetime, timedelta
from django.utils import timezone
from bookings.services import expire_booking
from showtimes.forms import ShowtimeForm

from django.http import JsonResponse

from showtimes.models import Showtime

from support.models import SupportTicket, SupportMessage



# Create your views here.

@staff_required
def dashboard(request):
    movie_count = Movie.objects.count()

    cinema_count = Cinema.objects.count()

    booking_count = Booking.objects.count()

    open_support_count = SupportTicket.objects.filter(
        status=SupportTicket.Status.OPEN
    ).count()

    context = {
        "movie_count": movie_count,
        "cinema_count": cinema_count,
        "booking_count": booking_count,
        "open_support_count": open_support_count,
    }


    return render(
        request,
        "staff/dashboard.html",
        context,
    )

# ============================================================
# MOVIES
# ============================================================

@staff_required
def movies(request):

    movie_list = Movie.objects.all().order_by(
        "-created_at"
    )

    form = StaffMovieForm()

    context = {
        "movies": movie_list,
        "form": form,
    }

    return render(
        request,
        "staff/movies.html",
        context,
    )


# ============================================================
# CREATE MOVIE
# ============================================================

@staff_required
def movie_create(request):

    if request.method != "POST":

        return redirect(
            "staff:movies"
        )

    form = StaffMovieForm(
        request.POST,
        request.FILES,
    )

    if form.is_valid():

        movie = form.save()

        messages.success(
            request,
            f'"{movie.title}" has been added successfully.',
        )

        return redirect(
            "staff:movies"
        )

    movie_list = Movie.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "staff/movies.html",
        {
            "movies": movie_list,
            "form": form,
            "add_movie_open": True,
        },
    )


# ============================================================
# EDIT MOVIE
# ============================================================

@staff_required
def movie_edit(request, pk):

    movie = get_object_or_404(
        Movie,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "staff:movies"
        )

    form = StaffMovieForm(
        request.POST,
        request.FILES,
        instance=movie,
    )

    if form.is_valid():

        movie = form.save()

        messages.success(
            request,
            f'"{movie.title}" has been updated successfully.',
        )

        return redirect(
            "staff:movies"
        )

    movie_list = Movie.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "staff/movies.html",
        {
            "movies": movie_list,
            "form": StaffMovieForm(),
            "edit_form": form,
            "edit_movie": movie,
            "edit_movie_open": True,
        },
    )


# ============================================================
# DELETE MOVIE
# ============================================================

@staff_required
def movie_delete(request, pk):

    movie = get_object_or_404(
        Movie,
        pk=pk,
    )

    if request.method == "POST":

        movie_title = movie.title

        try:

            movie.delete()

            messages.success(
                request,
                f'"{movie_title}" has been deleted successfully.',
            )

        except ProtectedError:

            messages.warning(
                request,
                (
                    f'"{movie_title}" cannot be deleted because '
                    f'it has existing showtimes or booking history. '
                    f'You can mark the movie as Ended instead.'
                ),
            )

    return redirect(
        "staff:movies"
    )

# ============================================================
# CINEMAS
# ============================================================

@staff_required
def cinemas(request):

    cinema_list = (
        Cinema.objects
        .prefetch_related("screens")
        .order_by("-created_at")
    )

    form = CinemaForm()

    context = {
        "cinemas": cinema_list,
        "form": form,
    }

    return render(
        request,
        "staff/cinemas.html",
        context,
    )


# ============================================================
# CREATE CINEMA
# ============================================================

@staff_required
def cinema_create(request):

    if request.method != "POST":

        return redirect(
            "staff:cinemas"
        )

    form = CinemaForm(
        request.POST
    )

    if form.is_valid():

        cinema = form.save()

        messages.success(
            request,
            f'"{cinema.name}" has been added successfully.',
        )

        return redirect(
            "staff:cinemas"
        )

    cinema_list = (
        Cinema.objects
        .prefetch_related("screens")
        .order_by("-created_at")
    )

    return render(
        request,
        "staff/cinemas.html",
        {
            "cinemas": cinema_list,
            "form": form,
            "add_cinema_open": True,
        },
    )


# ============================================================
# EDIT CINEMA
# ============================================================

@staff_required
def cinema_edit(request, pk):

    cinema = get_object_or_404(
        Cinema,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "staff:cinemas"
        )

    form = CinemaForm(
        request.POST,
        instance=cinema,
    )

    if form.is_valid():

        cinema = form.save()

        messages.success(
            request,
            f'"{cinema.name}" has been updated successfully.',
        )

        return redirect(
            "staff:cinemas"
        )

    cinema_list = (
        Cinema.objects
        .prefetch_related("screens")
        .order_by("-created_at")
    )

    return render(
        request,
        "staff/cinemas.html",
        {
            "cinemas": cinema_list,
            "form": CinemaForm(),
            "edit_form": form,
            "edit_cinema": cinema,
            "edit_cinema_open": True,
        },
    )


# ============================================================
# DELETE CINEMA
# ============================================================

@staff_required
def cinema_delete(request, pk):

    cinema = get_object_or_404(
        Cinema,
        pk=pk,
    )

    if request.method == "POST":

        cinema_name = cinema.name

        if cinema.screens.exists():

            messages.warning(
                request,
                (
                    f'"{cinema_name}" cannot be deleted because '
                    f'it still has screens. Remove or manage its '
                    f'screens first.'
                ),
            )

            return redirect(
                "staff:cinemas"
            )

        cinema.delete()

        messages.success(
            request,
            f'"{cinema_name}" has been deleted successfully.',
        )

    return redirect(
        "staff:cinemas"
    )

# ============================================================
# SCREEN LIST
# ============================================================

@staff_required
def screens(request, cinema_id):

    cinema = get_object_or_404(
        Cinema,
        pk=cinema_id,
    )

    screen_list = (
        Screen.objects
        .filter(cinema=cinema)
        .prefetch_related("seats")
        .order_by("name")
    )

    context = {
        "cinema": cinema,
        "screens": screen_list,

        # Add form
        "form": ScreenForm(),

        # Empty edit form for the reusable modal
        "edit_form": ScreenForm(),
    }

    return render(
        request,
        "staff/screens.html",
        context,
    )


# ============================================================
# SCREEN create
# ============================================================


@staff_required
def screen_create(request, cinema_id):

    cinema = get_object_or_404(
        Cinema,
        pk=cinema_id,
    )

    if request.method != "POST":

        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    form = ScreenForm(
        request.POST
    )


    if form.is_valid():

        screen = form.save(
            commit=False
        )

        screen.cinema = cinema

        screen.save()


        messages.success(
            request,
            f'"{screen.name}" has been added to {cinema.name}.',
        )


        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    screen_list = (
        Screen.objects
        .filter(cinema=cinema)
        .prefetch_related("seats")
        .order_by("name")
    )


    return render(
        request,
        "staff/screens.html",
        {
            "cinema": cinema,
            "screens": screen_list,
            "form": form,
            "edit_form": ScreenForm(),
            "add_screen_open": True,
        }
    )

# ============================================================
# EDIT SCREEN
# ============================================================

@staff_required
def screen_edit(request, pk):

    screen = get_object_or_404(
        Screen,
        pk=pk,
    )

    cinema = screen.cinema


    if request.method != "POST":

        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    form = ScreenForm(
        request.POST,
        instance=screen,
    )


    if form.is_valid():

        screen = form.save()

        messages.success(
            request,
            f'"{screen.name}" has been updated successfully.',
        )

        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    screen_list = (
        Screen.objects
        .filter(cinema=cinema)
        .prefetch_related("seats")
        .order_by("name")
    )


    return render(
        request,
        "staff/screens.html",
        {
            "cinema": cinema,
            "screens": screen_list,

            # Fresh add form
            "form": ScreenForm(),

            # THIS is the instance-bound form
            "edit_form": form,

            "edit_screen": screen,

            "edit_screen_open": True,
        },
    )
# ============================================================
# DELETE SCREEN
# ============================================================

@staff_required
def screen_delete(request, pk):

    screen = get_object_or_404(
        Screen,
        pk=pk,
    )

    cinema = screen.cinema


    if request.method != "POST":

        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    # ========================================================
    # PROTECTION
    # ========================================================

    if screen.seats.exists():

        messages.error(
            request,
            f'"{screen.name}" cannot be deleted because it has seats configured. Remove the seats first.',
        )

        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    if screen.showtimes.exists():

        messages.error(
            request,
            f'"{screen.name}" cannot be deleted because it has showtimes assigned to it.',
        )

        return redirect(
            "staff:screens",
            cinema_id=cinema.id,
        )


    # ========================================================
    # DELETE
    # ========================================================

    screen_name = screen.name

    screen.delete()


    messages.success(
        request,
        f'"{screen_name}" has been deleted successfully.',
    )


    return redirect(
        "staff:screens",
        cinema_id=cinema.id,
    )

# ============================================================
# SEAT LIST
# ============================================================

@staff_required
def seats(request, screen_id):

    screen = get_object_or_404(
        Screen,
        pk=screen_id,
    )

    cinema = screen.cinema


    seat_list = (
        Seat.objects
        .filter(screen=screen)
        .order_by(
            "row",
            "number",
        )
    )


    available_capacity = (
        screen.capacity -
        seat_list.count()
    )


    context = {

        "cinema": cinema,

        "screen": screen,

        "seats": seat_list,

        "available_capacity": available_capacity,

        "form": SeatForm(),

        "edit_form": SeatForm(),

        "generation_form": SeatGenerationForm(),

    }


    return render(
        request,
        "staff/seats.html",
        context,
    )

# ============================================================
# CREATE SEAT
# ============================================================

@staff_required
def seat_create(request, screen_id):

    screen = get_object_or_404(
        Screen,
        pk=screen_id,
    )

    cinema = screen.cinema


    if request.method != "POST":

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    form = SeatForm(
        request.POST
    )


    if form.is_valid():

        seat = form.save(
            commit=False
        )

        seat.screen = screen

        seat.save()


        messages.success(
            request,
            f'Seat "{seat.label}" has been added successfully.',
        )


        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    seat_list = (
        Seat.objects
        .filter(screen=screen)
        .order_by(
            "row",
            "number",
        )
    )


    return render(
        request,
        "staff/seats.html",
        {
            "cinema": cinema,

            "screen": screen,

            "seats": seat_list,

            "form": form,

            "edit_form": SeatForm(),

            "add_seat_open": True,
        },
    )

# ============================================================
# EDIT SEAT
# ============================================================

@staff_required
def seat_edit(request, pk):

    seat = get_object_or_404(
        Seat,
        pk=pk,
    )

    screen = seat.screen

    cinema = screen.cinema


    if request.method != "POST":

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    form = SeatForm(
        request.POST,
        instance=seat,
    )


    if form.is_valid():

        seat = form.save()


        messages.success(
            request,
            f'Seat "{seat.label}" has been updated successfully.',
        )


        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    seat_list = (
        Seat.objects
        .filter(screen=screen)
        .order_by(
            "row",
            "number",
        )
    )


    return render(
        request,
        "staff/seats.html",
        {
            "cinema": cinema,

            "screen": screen,

            "seats": seat_list,

            "form": SeatForm(),

            "edit_form": form,

            "edit_seat": seat,

            "edit_seat_open": True,
        },
    )

# ============================================================
# DELETE SEAT
# ============================================================

@staff_required
def seat_delete(request, pk):

    seat = get_object_or_404(
        Seat,
        pk=pk,
    )

    screen = seat.screen


    if request.method != "POST":

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    # ========================================================
    # PROTECT BOOKED SEATS
    # ========================================================

    if seat.booking_seats.exists():

        messages.error(
            request,
            f'Seat "{seat.label}" cannot be deleted because it has booking records.',
        )

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    seat_label = seat.label


    seat.delete()


    messages.success(
        request,
        f'Seat "{seat_label}" has been deleted successfully.',
    )


    return redirect(
        "staff:seats",
        screen_id=screen.id,
    )

# ============================================================
# GENERATE SEATS
# ============================================================

@staff_required
def generate_seats(request, screen_id):

    screen = get_object_or_404(
        Screen,
        pk=screen_id,
    )

    cinema = screen.cinema


    if request.method != "POST":

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    form = SeatGenerationForm(
        request.POST
    )


    if not form.is_valid():

        seat_list = (
            Seat.objects
            .filter(screen=screen)
            .order_by(
                "row",
                "number",
            )
        )


        return render(
            request,
            "staff/seats.html",
            {
                "cinema": cinema,

                "screen": screen,

                "seats": seat_list,

                "available_capacity": (
                    screen.capacity -
                    seat_list.count()
                ),

                "form": SeatForm(),

                "edit_form": SeatForm(),

                "generation_form": form,

                "generate_seats_open": True,
            },
        )


    start_row = (
        form.cleaned_data["start_row"]
        .strip()
        .upper()
    )

    end_row = (
        form.cleaned_data["end_row"]
        .strip()
        .upper()
    )

    seats_per_row = (
        form.cleaned_data["seats_per_row"]
    )


    # ========================================================
    # VALIDATE ROWS
    # ========================================================

    if (
        len(start_row) != 1
        or len(end_row) != 1
        or not start_row.isalpha()
        or not end_row.isalpha()
    ):

        messages.error(
            request,
            "Rows must be single letters, for example A to F.",
        )

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    start_number = ord(start_row)

    end_number = ord(end_row)


    if start_number > end_number:

        messages.error(
            request,
            "Starting row must come before the ending row.",
        )

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    # ========================================================
    # BUILD ROWS
    # ========================================================

    rows = [
        chr(number)
        for number in range(
            start_number,
            end_number + 1,
        )
    ]


    requested_seat_count = (
        len(rows) *
        seats_per_row
    )


    existing_count = (
        Seat.objects
        .filter(screen=screen)
        .count()
    )


    # ========================================================
    # CAPACITY CHECK
    # ========================================================

    if (
        existing_count +
        requested_seat_count
        > screen.capacity
    ):

        available_capacity = (
            screen.capacity -
            existing_count
        )


        messages.error(
            request,
            (
                f"You are trying to generate "
                f"{requested_seat_count} seats, "
                f"but this screen only has "
                f"{available_capacity} available spaces."
            ),
        )

        return redirect(
            "staff:seats",
            screen_id=screen.id,
        )


    # ========================================================
    # CREATE MISSING SEATS
    # ========================================================

    existing_seats = set(
        Seat.objects
        .filter(
            screen=screen,
            row__in=rows,
        )
        .values_list(
            "row",
            "number",
        )
    )


    seats_to_create = []


    for row in rows:

        for number in range(
            1,
            seats_per_row + 1,
        ):

            if (
                row,
                number,
            ) in existing_seats:

                continue


            seats_to_create.append(
                Seat(
                    screen=screen,
                    row=row,
                    number=number,
                    is_active=True,
                )
            )


    if seats_to_create:

        Seat.objects.bulk_create(
            seats_to_create
        )


    created_count = len(
        seats_to_create
    )


    if created_count:

        messages.success(
            request,
            (
                f"{created_count} seat"
                f"{'s' if created_count != 1 else ''} "
                f"generated successfully."
            ),
        )

    else:

        messages.info(
            request,
            "All requested seats already exist.",
        )


    return redirect(
        "staff:seats",
        screen_id=screen.id,
    )


# ============================================================
# SHOWTIMES
# ============================================================

@staff_required
def showtimes(request):

    showtimes = (
        Showtime.objects
        .select_related(
            "movie",
            "screen",
            "screen__cinema",
        )
        .order_by(
            "show_date",
            "start_time",
            "movie__title",
        )
    )


    # ========================================================
    # SEARCH
    # ========================================================

    search_query = request.GET.get(
        "search",
        ""
    ).strip()


    if search_query:

        showtimes = showtimes.filter(

            Q(
                movie__title__icontains=search_query
            )

            |

            Q(
                screen__name__icontains=search_query
            )

            |

            Q(
                screen__cinema__name__icontains=search_query
            )

        )


    # ========================================================
    # CINEMA FILTER
    # ========================================================

    cinema_id = request.GET.get(
        "cinema",
        ""
    ).strip()


    if cinema_id:

        showtimes = showtimes.filter(
            screen__cinema_id=cinema_id
        )


    # ========================================================
    # STATUS FILTER
    # ========================================================

    status = request.GET.get(
        "status",
        ""
    ).strip()


    if status in dict(
        Showtime.Status.choices
    ):

        showtimes = showtimes.filter(
            status=status
        )


    # ========================================================
    # DATE FILTER
    # ========================================================

    show_date = request.GET.get(
        "date",
        ""
    ).strip()


    if show_date:

        showtimes = showtimes.filter(
            show_date=show_date
        )


    # ========================================================
    # FILTER OPTIONS
    # ========================================================

    cinemas = (
        Cinema.objects
        .filter(
            is_active=True
        )
        .order_by(
            "name"
        )
    )


    form = ShowtimeForm()


    context = {

    "showtimes": showtimes,

    "form": form,

    "cinemas": cinemas,

    "showtime_status_choices": (
        Showtime.Status.choices
    ),

    "search_query": search_query,

    "selected_cinema": cinema_id,

    "selected_status": status,

    "selected_date": show_date,

    }


    return render(
        request,
        "staff/showtimes.html",
        context,
    )


# ============================================================
# CREATE SHOWTIME
# ============================================================

@staff_required
def showtime_create(request):

    if request.method != "POST":

        return redirect(
            "staff:showtimes"
        )

    form = ShowtimeForm(
        request.POST
    )

    if form.is_valid():

        showtime = form.save(
            commit=False
        )

        # ----------------------------------------------------
        # CHECK FOR SCREEN CONFLICT
        # ----------------------------------------------------

        conflict = get_showtime_conflict(
            showtime
        )

        if conflict:

            form.add_error(
                "start_time",
                (
                    "This screen already has a showtime "
                    f"from "
                    f"{conflict.start_time.strftime('%H:%M')} "
                    f"to "
                    f"{conflict.end_time.strftime('%H:%M')} "
                    "on this date."
                ),
            )

        else:

            showtime.save()

            messages.success(
                request,
                (
                    f'Showtime for "{showtime.movie.title}" '
                    "has been added successfully."
                ),
            )

            return redirect(
                "staff:showtimes"
            )

    # --------------------------------------------------------
    # FORM ERROR
    # --------------------------------------------------------

    showtime_list = (
        Showtime.objects
        .select_related(
            "movie",
            "screen",
            "screen__cinema",
        )
        .order_by(
            "-show_date",
            "start_time",
            "movie__title",
        )
    )

    return render(
        request,
        "staff/showtimes.html",
        {
            "showtimes": showtime_list,

            "form": form,

            "add_showtime_open": True,
        },
    )


# ============================================================
# EDIT SHOWTIME
# ============================================================

@staff_required
def showtime_edit(request, pk):

    showtime = get_object_or_404(
        Showtime.objects.select_related(
            "movie",
            "screen",
            "screen__cinema",
        ),
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "staff:showtimes"
        )

    form = ShowtimeForm(
        request.POST,
        instance=showtime,
    )

    if form.is_valid():

        updated_showtime = form.save(
            commit=False
        )

        # ----------------------------------------------------
        # CHECK FOR SCREEN CONFLICT
        # ----------------------------------------------------

        conflict = get_showtime_conflict(
            updated_showtime,
            exclude_pk=showtime.pk,
        )

        if conflict:

            form.add_error(
                "start_time",
                (
                    "This screen already has a showtime "
                    f"from "
                    f"{conflict.start_time.strftime('%H:%M')} "
                    f"to "
                    f"{conflict.end_time.strftime('%H:%M')} "
                    "on this date."
                ),
            )

        else:

            updated_showtime.save()

            messages.success(
                request,
                (
                    f'Showtime for '
                    f'"{updated_showtime.movie.title}" '
                    "has been updated successfully."
                ),
            )

            return redirect(
                "staff:showtimes"
            )

    # --------------------------------------------------------
    # FORM ERROR
    # --------------------------------------------------------

    showtime_list = (
        Showtime.objects
        .select_related(
            "movie",
            "screen",
            "screen__cinema",
        )
        .order_by(
            "-show_date",
            "start_time",
            "movie__title",
        )
    )

    return render(
        request,
        "staff/showtimes.html",
        {
            "showtimes": showtime_list,

            # Fresh Add Showtime form
            "form": ShowtimeForm(),

            # Instance-bound Edit form
            "edit_form": form,

            "edit_showtime": showtime,

            "edit_showtime_open": True,
        },
    )


# ============================================================
# CANCEL SHOWTIME
# ============================================================

@staff_required
def showtime_cancel(request, pk):

    showtime = get_object_or_404(
        Showtime,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "staff:showtimes"
        )

    # --------------------------------------------------------
    # ALREADY CANCELLED
    # --------------------------------------------------------

    if showtime.status == Showtime.Status.CANCELLED:

        messages.warning(
            request,
            "This showtime is already cancelled.",
        )

        return redirect(
            "staff:showtimes"
        )

    # --------------------------------------------------------
    # COMPLETED SHOWTIME
    # --------------------------------------------------------

    if showtime.status == Showtime.Status.COMPLETED:

        messages.error(
            request,
            "A completed showtime cannot be cancelled.",
        )

        return redirect(
            "staff:showtimes"
        )

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    showtime.status = Showtime.Status.CANCELLED

    showtime.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            f'Showtime for "{showtime.movie.title}" '
            "has been cancelled successfully."
        ),
    )

    return redirect(
        "staff:showtimes"
    )


# ============================================================
# DELETE SHOWTIME
# ============================================================

@staff_required
def showtime_delete(request, pk):

    showtime = get_object_or_404(
        Showtime,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "staff:showtimes"
        )

    movie_title = showtime.movie.title

    try:

        showtime.delete()

        messages.success(
            request,
            (
                f'Showtime for "{movie_title}" '
                "has been deleted successfully."
            ),
        )

    except ProtectedError:

        messages.warning(
            request,
            (
                f'Showtime for "{movie_title}" cannot be deleted '
                "because it has existing bookings. "
                "Cancel the showtime instead."
            ),
        )

    return redirect(
        "staff:showtimes"
    )


# ============================================================
# CINEMA → SCREEN OPTIONS
# ============================================================

@staff_required
def cinema_screens(request, cinema_id):

    cinema = get_object_or_404(
        Cinema,
        pk=cinema_id,
        is_active=True,
    )

    screens = (
        Screen.objects
        .filter(
            cinema=cinema,
            is_active=True,
        )
        .order_by("name")
    )

    data = [
        {
            "id": screen.id,
            "name": screen.name,
            "screen_type": screen.get_screen_type_display(),
            "capacity": screen.capacity,
        }
        for screen in screens
    ]

    return JsonResponse(
        {
            "cinema": cinema.name,
            "screens": data,
        }
    )


# ============================================================
# SHOWTIME CONFLICT CHECK
# ============================================================

def get_showtime_conflict(
    showtime,
    exclude_pk=None,
):

    if not all(
        [
            showtime.screen,
            showtime.show_date,
            showtime.start_time,
            showtime.movie,
        ]
    ):

        return None

    # --------------------------------------------------------
    # NEW SHOWTIME START
    # --------------------------------------------------------

    new_start = datetime.combine(
        showtime.show_date,
        showtime.start_time,
    )

    # --------------------------------------------------------
    # NEW SHOWTIME END
    # --------------------------------------------------------

    new_end = (
        new_start
        + timedelta(
            minutes=showtime.movie.duration
        )
    )

    # --------------------------------------------------------
    # EXISTING SHOWTIMES
    # --------------------------------------------------------

    existing_showtimes = (
        Showtime.objects
        .filter(
            screen=showtime.screen,
            show_date=showtime.show_date,
        )
        .exclude(
            status=Showtime.Status.CANCELLED,
        )
    )

    # --------------------------------------------------------
    # DON'T COMPARE AN EDIT AGAINST ITSELF
    # --------------------------------------------------------

    if exclude_pk:

        existing_showtimes = (
            existing_showtimes
            .exclude(pk=exclude_pk)
        )

    # --------------------------------------------------------
    # CHECK OVERLAP
    # --------------------------------------------------------

    for existing in existing_showtimes:

        existing_start = datetime.combine(
            existing.show_date,
            existing.start_time,
        )

        existing_end = (
            existing_start
            + timedelta(
                minutes=existing.movie.duration
            )
        )

        # ----------------------------------------------------
        # OVERLAP CONDITION
        # ----------------------------------------------------

        if (
            new_start < existing_end
            and
            new_end > existing_start
        ):

            return existing

    return None


# ============================================================
# BOOKINGS
# ============================================================

@staff_required
def bookings(request):

    # ========================================================
    # EXPIRE OLD HELD BOOKINGS
    #
    # This makes the staff booking list reflect the real
    # booking lifecycle whenever the page is opened.
    # ========================================================

    now = timezone.now()

    expired_bookings = (
        Booking.objects
        .filter(
            status=Booking.Status.HELD,
            hold_expires_at__isnull=False,
            hold_expires_at__lte=now,
        )
    )

    for booking in expired_bookings:

        expire_booking(
            booking
        )


    # ========================================================
    # BASE QUERYSET
    # ========================================================

    bookings = (
        Booking.objects
        .select_related(
            "user",
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


    # ========================================================
    # SEARCH
    # ========================================================

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    if search_query:

        bookings = bookings.filter(

            Q(
                booking_reference__icontains=
                search_query
            )

            |

            Q(
                user__username__icontains=
                search_query
            )

            |

            Q(
                user__first_name__icontains=
                search_query
            )

            |

            Q(
                user__last_name__icontains=
                search_query
            )

            |

            Q(
                user__email__icontains=
                search_query
            )

            |

            Q(
                showtime__movie__title__icontains=
                search_query
            )

        )


    # ========================================================
    # STATUS FILTER
    # ========================================================

    status_filter = request.GET.get(
        "status",
        ""
    ).strip()

    valid_statuses = {
        choice[0]
        for choice in Booking.Status.choices
    }

    if status_filter in valid_statuses:

        bookings = bookings.filter(
            status=status_filter
        )


    # ========================================================
    # CINEMA FILTER
    # ========================================================

    cinema_filter = request.GET.get(
        "cinema",
        ""
    ).strip()

    if cinema_filter:

        try:

            cinema_id = int(
                cinema_filter
            )

            bookings = bookings.filter(
                showtime__screen__cinema_id=
                cinema_id
            )

        except (
            TypeError,
            ValueError,
        ):

            cinema_filter = ""


    # ========================================================
    # DATE FILTER
    # ========================================================

    show_date = request.GET.get(
        "show_date",
        ""
    ).strip()

    if show_date:

        bookings = bookings.filter(
            showtime__show_date=show_date
        )


    # ========================================================
    # CINEMA OPTIONS
    # ========================================================

    cinemas = (
        Cinema.objects
        .filter(
            is_active=True,
        )
        .order_by(
            "name",
        )
    )


    # ========================================================
    # COUNTS
    # ========================================================

    total_bookings = bookings.count()

    held_count = bookings.filter(
        status=Booking.Status.HELD
    ).count()

    confirmed_count = bookings.filter(
        status=Booking.Status.CONFIRMED
    ).count()

    cancelled_count = bookings.filter(
        status=Booking.Status.CANCELLED
    ).count()

    expired_count = bookings.filter(
        status=Booking.Status.EXPIRED
    ).count()


    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        "bookings": bookings,

        "cinemas": cinemas,

        "total_bookings": total_bookings,

        "held_count": held_count,

        "confirmed_count": confirmed_count,

        "cancelled_count": cancelled_count,

        "expired_count": expired_count,

        "search_query": search_query,

        "status_filter": status_filter,

        "cinema_filter": cinema_filter,

        "show_date": show_date,

    }


    return render(
        request,
        "staff/bookings.html",
        context,
    )

# ============================================================
# SUPPORT — TICKET LIST
# ============================================================
# ============================================================
# SUPPORT — STAFF TICKET MANAGEMENT
# ============================================================

@staff_required
def support(request):

    # ========================================================
    # HANDLE STAFF ACTIONS
    # ========================================================

    if request.method == "POST":

        action = request.POST.get(
            "action",
            "",
        )

        ticket_id = request.POST.get(
            "ticket_id",
            "",
        )

        ticket = get_object_or_404(
            SupportTicket,
            id=ticket_id,
        )


        # ====================================================
        # REPLY TO TICKET
        # ====================================================

        if action == "reply":

            # -----------------------------------------------
            # CLOSED TICKET
            # -----------------------------------------------

            if (
                ticket.status
                == SupportTicket.Status.CLOSED
            ):

                messages.error(
                    request,
                    (
                        "This ticket is closed and "
                        "cannot receive new replies."
                    ),
                )

                return redirect(
                    "staff:support"
                )


            form = SupportReplyForm(
                request.POST
            )


            if form.is_valid():

                support_message = form.save(
                    commit=False
                )

                support_message.ticket = ticket

                support_message.sender = request.user

                support_message.save()


                # -------------------------------------------
                # UPDATE STATUS
                # -------------------------------------------

                ticket.status = (
                    SupportTicket.Status.IN_PROGRESS
                )

                ticket.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )


                messages.success(
                    request,
                    "Reply sent successfully.",
                )

            else:

                messages.error(
                    request,
                    "Please enter a valid reply.",
                )


        # ====================================================
        # UPDATE STATUS
        # ====================================================

        elif action == "status":

            new_status = request.POST.get(
                "status",
                "",
            )


            valid_statuses = {
                value
                for value, label
                in SupportTicket.Status.choices
            }


            if new_status not in valid_statuses:

                messages.error(
                    request,
                    "Invalid support ticket status.",
                )

            else:

                ticket.status = new_status

                ticket.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )


                messages.success(
                    request,
                    "Support ticket status updated successfully.",
                )


        # ====================================================
        # UPDATE PRIORITY
        # ====================================================

        elif action == "priority":

            new_priority = request.POST.get(
                "priority",
                "",
            )


            valid_priorities = {
                value
                for value, label
                in SupportTicket.Priority.choices
            }


            if new_priority not in valid_priorities:

                messages.error(
                    request,
                    "Invalid support ticket priority.",
                )

            else:

                ticket.priority = new_priority

                ticket.save(
                    update_fields=[
                        "priority",
                        "updated_at",
                    ]
                )


                messages.success(
                    request,
                    "Support ticket priority updated successfully.",
                )


        else:

            messages.error(
                request,
                "Invalid support action.",
            )


        return redirect(
            "staff:support"
        )


    # ========================================================
    # BASE QUERYSET
    # ========================================================

    tickets = (
        SupportTicket.objects
        .select_related(
            "customer",
            "booking",
            "booking__showtime",
            "booking__showtime__movie",
            "booking__showtime__screen",
            "booking__showtime__screen__cinema",
        )
        .prefetch_related(
            "messages__sender",
        )
        .order_by(
            "-updated_at",
        )
    )


    # ========================================================
    # SEARCH
    # ========================================================

    search = request.GET.get(
        "search",
        "",
    ).strip()


    if search:

        tickets = tickets.filter(

            Q(
                subject__icontains=search
            )

            |

            Q(
                customer__username__icontains=search
            )

            |

            Q(
                customer__first_name__icontains=search
            )

            |

            Q(
                customer__last_name__icontains=search
            )

            |

            Q(
                customer__email__icontains=search
            )

            |

            Q(
                booking__booking_reference__icontains=search
            )

        )


    # ========================================================
    # STATUS FILTER
    # ========================================================

    status = request.GET.get(
        "status",
        "",
    ).strip()


    valid_statuses = {
        value
        for value, label
        in SupportTicket.Status.choices
    }


    if status in valid_statuses:

        tickets = tickets.filter(
            status=status
        )

    else:

        status = ""


    # ========================================================
    # PRIORITY FILTER
    # ========================================================

    priority = request.GET.get(
        "priority",
        "",
    ).strip()


    valid_priorities = {
        value
        for value, label
        in SupportTicket.Priority.choices
    }


    if priority in valid_priorities:

        tickets = tickets.filter(
            priority=priority
        )

    else:

        priority = ""


    # ========================================================
    # SUPPORT COUNTS
    # ========================================================

    open_count = (
        SupportTicket.objects
        .filter(
            status=SupportTicket.Status.OPEN
        )
        .count()
    )


    in_progress_count = (
        SupportTicket.objects
        .filter(
            status=SupportTicket.Status.IN_PROGRESS
        )
        .count()
    )


    waiting_count = (
        SupportTicket.objects
        .filter(
            status=(
                SupportTicket.Status.WAITING_FOR_CUSTOMER
            )
        )
        .count()
    )


    resolved_count = (
        SupportTicket.objects
        .filter(
            status=SupportTicket.Status.RESOLVED
        )
        .count()
    )


    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        "tickets": tickets,

        "search": search,

        "status": status,

        "priority": priority,

        "status_choices": (
            SupportTicket.Status.choices
        ),

        "priority_choices": (
            SupportTicket.Priority.choices
        ),

        "open_count": open_count,

        "in_progress_count": (
            in_progress_count
        ),

        "waiting_count": waiting_count,

        "resolved_count": resolved_count,

        "form": SupportReplyForm(),

    }


    return render(
        request,
        "staff/support.html",
        context,
    )


# ============================================================
# SUPPORT — UPDATE STATUS
# ============================================================

@staff_required
def support_ticket_status(
    request,
    ticket_id,
):

    ticket = get_object_or_404(
        SupportTicket,
        id=ticket_id,
    )


    if request.method != "POST":

        return redirect(
            "staff:support"
        )


    status = request.POST.get(
        "status",
        "",
    )


    valid_statuses = {
        value
        for value, label
        in SupportTicket.Status.choices
    }


    if status not in valid_statuses:

        messages.error(
            request,
            "Invalid support ticket status.",
        )

        return redirect(
            "staff:support"
        )


    ticket.status = status

    ticket.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )


    messages.success(
        request,
        "Support ticket status updated successfully.",
    )


    return redirect(
        "staff:support"
    )


# ============================================================
# SUPPORT — UPDATE PRIORITY
# ============================================================

@staff_required
def support_ticket_priority(
    request,
    ticket_id,
):

    ticket = get_object_or_404(
        SupportTicket,
        id=ticket_id,
    )


    if request.method != "POST":

        return redirect(
            "staff:support"
        )


    priority = request.POST.get(
        "priority",
        "",
    )


    valid_priorities = {
        value
        for value, label
        in SupportTicket.Priority.choices
    }


    if priority not in valid_priorities:

        messages.error(
            request,
            "Invalid support ticket priority.",
        )

        return redirect(
            "staff:support"
        )


    ticket.priority = priority

    ticket.save(
        update_fields=[
            "priority",
            "updated_at",
        ]
    )


    messages.success(
        request,
        "Support ticket priority updated successfully.",
    )


    return redirect(
        "staff:support"
    )

# ============================================================
# CUSTOMERS
# ============================================================

@staff_required
def customers(request):

    # ========================================================
    # SEARCH
    # ========================================================

    search = request.GET.get(
        "search",
        "",
    ).strip()

    # ========================================================
    # STATUS
    # ========================================================

    status = request.GET.get(
        "status",
        "",
    ).strip()

    # ========================================================
    # CUSTOMER QUERYSET
    # ========================================================

    customers = (
        User.objects
        .filter(
            is_staff=False,
            is_superuser=False,
        )
        .prefetch_related(
            Prefetch(
                "bookings",
                queryset=(
                    Booking.objects
                    .select_related(
                        "showtime",
                        "showtime__movie",
                        "showtime__screen",
                        "showtime__screen__cinema",
                    )
                    .order_by(
                        "-created_at",
                    )
                ),
                to_attr="staff_bookings",
            ),
            Prefetch(
                "support_tickets",
                queryset=(
                    SupportTicket.objects
                    .order_by(
                        "-updated_at",
                    )
                ),
                to_attr="staff_support_tickets",
            ),
        )
        .annotate(
            booking_count=Count(
                "bookings",
                distinct=True,
            ),
            support_count=Count(
                "support_tickets",
                distinct=True,
            ),
        )
        .order_by(
            "-date_joined",
        )
    )

    # ========================================================
    # SEARCH FILTER
    # ========================================================

    if search:

        customers = customers.filter(
            Q(
                username__icontains=search
            )
            |
            Q(
                first_name__icontains=search
            )
            |
            Q(
                last_name__icontains=search
            )
            |
            Q(
                email__icontains=search
            )
        )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    if status == "active":

        customers = customers.filter(
            is_active=True,
        )

    elif status == "inactive":

        customers = customers.filter(
            is_active=False,
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    customer_queryset = User.objects.filter(
        is_staff=False,
        is_superuser=False,
    )

    total_customers = customer_queryset.count()

    active_customers = customer_queryset.filter(
        is_active=True,
    ).count()

    inactive_customers = customer_queryset.filter(
        is_active=False,
    ).count()

    customer_booking_count = (
        Booking.objects
        .values("user")
        .distinct()
        .count()
    )

    customer_support_count = (
        SupportTicket.objects
        .values("customer")
        .distinct()
        .count()
    )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        "customers": customers,

        "total_customers": total_customers,

        "active_customers": active_customers,

        "inactive_customers": inactive_customers,

        "customer_booking_count": (
            customer_booking_count
        ),

        "customer_support_count": (
            customer_support_count
        ),

        "search": search,

        "status": status,

    }

    return render(
        request,
        "staff/customers.html",
        context,
    )

# ============================================================
# SCREENS OVERVIEW
# ============================================================

@staff_required
def screens_overview(request):

    cinemas = (
        Cinema.objects
        .filter(
            is_active=True,
        )
        .prefetch_related(
            "screens",
        )
        .order_by(
            "name",
        )
    )

    return render(
        request,
        "staff/screens_overview.html",
        {
            "cinemas": cinemas,
        },
    )