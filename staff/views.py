from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import ProtectedError

from .decorators import staff_required

from movies.models import Movie
from movies.forms import StaffMovieForm
from cinemas.models import Cinema,Screen,Seat
from cinemas.forms import CinemaForm,ScreenForm,SeatForm,SeatGenerationForm
from bookings.models import Booking

from support.models import SupportTicket

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