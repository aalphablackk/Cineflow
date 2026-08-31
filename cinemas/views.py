from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import IntegrityError, transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import (
    CinemaForm,
    ScreenForm,
    SeatForm,
)

from .models import (
    Cinema,
    Screen,
    Seat,
)


# ============================================================
# STAFF ACCESS
# ============================================================

def staff_required(user):
    """
    Allow access only to authenticated staff users.
    """

    return (
        user.is_authenticated
        and user.is_staff
    )


# ============================================================
# CUSTOMER PAGES
# ============================================================

def cinema_list(request):
    """
    Display all active cinemas to customers.
    """

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
        "cinemas/cinema_list.html",
        {
            "cinemas": cinemas,
        },
    )


# ============================================================
# CINEMA DETAIL
# ============================================================

def cinema_detail(request, slug):
    """
    Display an active cinema and its active screens.
    """

    cinema = get_object_or_404(
        Cinema.objects.prefetch_related(
            "screens",
        ),
        slug=slug,
        is_active=True,
    )

    screens = [
        screen
        for screen in cinema.screens.all()
        if screen.is_active
    ]

    return render(
        request,
        "cinemas/cinema_detail.html",
        {
            "cinema": cinema,
            "screens": screens,
            "active_screen_count": len(screens),
        },
    )


# ============================================================
# CREATE CINEMA
# ============================================================

@user_passes_test(staff_required)
def create_cinema(request):

    if request.method == "POST":

        form = CinemaForm(
            request.POST,
        )

        if form.is_valid():

            cinema = form.save()

            messages.success(
                request,
                f"{cinema.name} was created successfully.",
            )

            return redirect(
                "cinemas:cinema_detail",
                slug=cinema.slug,
            )

    else:

        form = CinemaForm()


    return render(
        request,
        "cinemas/cinema_form.html",
        {
            "form": form,
            "page_title": "Add Cinema",
            "submit_text": "Create Cinema",
        },
    )


# ============================================================
# EDIT CINEMA
# ============================================================

@user_passes_test(staff_required)
def edit_cinema(request, cinema_id):

    cinema = get_object_or_404(
        Cinema,
        id=cinema_id,
    )

    if request.method == "POST":

        form = CinemaForm(
            request.POST,
            instance=cinema,
        )

        if form.is_valid():

            cinema = form.save()

            messages.success(
                request,
                f"{cinema.name} was updated successfully.",
            )

            return redirect(
                "cinemas:cinema_detail",
                slug=cinema.slug,
            )

    else:

        form = CinemaForm(
            instance=cinema,
        )


    return render(
        request,
        "cinemas/cinema_form.html",
        {
            "form": form,
            "cinema": cinema,
            "page_title": "Edit Cinema",
            "submit_text": "Save Changes",
        },
    )


# ============================================================
# DELETE CINEMA
# ============================================================

@user_passes_test(staff_required)
def delete_cinema(request, cinema_id):

    cinema = get_object_or_404(
        Cinema,
        id=cinema_id,
    )

    if request.method == "POST":

        cinema_name = cinema.name

        cinema.delete()

        messages.success(
            request,
            f"{cinema_name} was deleted successfully.",
        )

        return redirect(
            "cinemas:cinema_list",
        )


    return render(
        request,
        "cinemas/cinema_confirm_delete.html",
        {
            "cinema": cinema,
        },
    )


# ============================================================
# CREATE SCREEN
# ============================================================

@user_passes_test(staff_required)
def create_screen(request):

    if request.method == "POST":

        form = ScreenForm(
            request.POST,
        )

        if form.is_valid():

            screen = form.save()

            messages.success(
                request,
                f"{screen.name} was created successfully.",
            )

            return redirect(
                "cinemas:cinema_detail",
                slug=screen.cinema.slug,
            )

    else:

        form = ScreenForm()


    return render(
        request,
        "cinemas/screen_form.html",
        {
            "form": form,
            "page_title": "Add Screen",
            "submit_text": "Create Screen",
        },
    )


# ============================================================
# EDIT SCREEN
# ============================================================

@user_passes_test(staff_required)
def edit_screen(request, screen_id):

    screen = get_object_or_404(
        Screen.objects.select_related(
            "cinema",
        ),
        id=screen_id,
    )

    if request.method == "POST":

        form = ScreenForm(
            request.POST,
            instance=screen,
        )

        if form.is_valid():

            screen = form.save()

            messages.success(
                request,
                f"{screen.name} was updated successfully.",
            )

            return redirect(
                "cinemas:cinema_detail",
                slug=screen.cinema.slug,
            )

    else:

        form = ScreenForm(
            instance=screen,
        )


    return render(
        request,
        "cinemas/screen_form.html",
        {
            "form": form,
            "screen": screen,
            "page_title": "Edit Screen",
            "submit_text": "Save Changes",
        },
    )


# ============================================================
# DELETE SCREEN
# ============================================================

@user_passes_test(staff_required)
def delete_screen(request, screen_id):

    screen = get_object_or_404(
        Screen.objects.select_related(
            "cinema",
        ),
        id=screen_id,
    )

    cinema_slug = screen.cinema.slug

    if request.method == "POST":

        screen_name = screen.name

        screen.delete()

        messages.success(
            request,
            f"{screen_name} was deleted successfully.",
        )

        return redirect(
            "cinemas:cinema_detail",
            slug=cinema_slug,
        )


    return render(
        request,
        "cinemas/screen_confirm_delete.html",
        {
            "screen": screen,
        },
    )


# ============================================================
# SEAT LIST
# ============================================================

@user_passes_test(staff_required)
def seat_list(request, screen_id):

    screen = get_object_or_404(
        Screen.objects.select_related(
            "cinema",
        ),
        id=screen_id,
    )

    seats = (
        screen.seats
        .all()
        .order_by(
            "row",
            "number",
        )
    )

    active_seat_count = (
        seats
        .filter(
            is_active=True,
        )
        .count()
    )

    inactive_seat_count = (
        seats
        .filter(
            is_active=False,
        )
        .count()
    )

    return render(
        request,
        "cinemas/seat_list.html",
        {
            "screen": screen,
            "seats": seats,
            "active_seat_count": active_seat_count,
            "inactive_seat_count": inactive_seat_count,
            "seat_count": seats.count(),
        },
    )


# ============================================================
# CREATE SINGLE SEAT
# ============================================================

@user_passes_test(staff_required)
def create_seat(request, screen_id):

    screen = get_object_or_404(
        Screen.objects.select_related(
            "cinema",
        ),
        id=screen_id,
    )

    if request.method == "POST":

        form = SeatForm(
            request.POST,
        )

        if form.is_valid():

            seat = form.save(
                commit=False,
            )

            seat.screen = screen

            try:

                seat.save()

                messages.success(
                    request,
                    f"Seat {seat.label} was created successfully.",
                )

                return redirect(
                    "cinemas:seat_list",
                    screen_id=screen.id,
                )

            except IntegrityError:

                form.add_error(
                    None,
                    "This seat already exists on this screen.",
                )

    else:

        form = SeatForm(
            initial={
                "screen": screen,
            },
        )


    return render(
        request,
        "cinemas/seat_form.html",
        {
            "form": form,
            "screen": screen,
            "page_title": "Add Seat",
            "submit_text": "Create Seat",
        },
    )


# ============================================================
# EDIT SEAT
# ============================================================

@user_passes_test(staff_required)
def edit_seat(request, seat_id):

    seat = get_object_or_404(
        Seat.objects.select_related(
            "screen",
            "screen__cinema",
        ),
        id=seat_id,
    )

    screen = seat.screen

    if request.method == "POST":

        form = SeatForm(
            request.POST,
            instance=seat,
        )

        if form.is_valid():

            seat = form.save(
                commit=False,
            )

            seat.screen = screen

            try:

                seat.save()

                messages.success(
                    request,
                    f"Seat {seat.label} was updated successfully.",
                )

                return redirect(
                    "cinemas:seat_list",
                    screen_id=screen.id,
                )

            except IntegrityError:

                form.add_error(
                    None,
                    "This seat already exists on this screen.",
                )

    else:

        form = SeatForm(
            instance=seat,
        )


    return render(
        request,
        "cinemas/seat_form.html",
        {
            "form": form,
            "seat": seat,
            "screen": screen,
            "page_title": "Edit Seat",
            "submit_text": "Save Changes",
        },
    )


# ============================================================
# DELETE SEAT
# ============================================================

@user_passes_test(staff_required)
def delete_seat(request, seat_id):

    seat = get_object_or_404(
        Seat.objects.select_related(
            "screen",
            "screen__cinema",
        ),
        id=seat_id,
    )

    screen = seat.screen

    if request.method == "POST":

        seat_label = seat.label

        seat.delete()

        messages.success(
            request,
            f"Seat {seat_label} was deleted successfully.",
        )

        return redirect(
            "cinemas:seat_list",
            screen_id=screen.id,
        )


    return render(
        request,
        "cinemas/seat_confirm_delete.html",
        {
            "seat": seat,
            "screen": screen,
        },
    )


# ============================================================
# GENERATE SEATS
# ============================================================

@user_passes_test(staff_required)
def generate_seats(request, screen_id):

    screen = get_object_or_404(
        Screen.objects.select_related(
            "cinema",
        ),
        id=screen_id,
    )

    if request.method == "POST":

        start_row = (
            request.POST
            .get(
                "start_row",
                "A",
            )
            .strip()
            .upper()
        )

        end_row = (
            request.POST
            .get(
                "end_row",
                "A",
            )
            .strip()
            .upper()
        )

        seats_per_row = request.POST.get(
            "seats_per_row",
        )


        # ====================================================
        # VALIDATE ROWS
        # ====================================================

        if (
            not start_row
            or not end_row
            or len(start_row) > 5
            or len(end_row) > 5
        ):

            messages.error(
                request,
                "Please enter valid starting and ending rows.",
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        # ====================================================
        # VALIDATE ROW CHARACTERS
        # ====================================================

        if (
            not start_row.isalpha()
            or not end_row.isalpha()
        ):

            messages.error(
                request,
                "Rows must contain letters only.",
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        # ====================================================
        # VALIDATE SEATS PER ROW
        # ====================================================

        try:

            seats_per_row = int(
                seats_per_row,
            )

        except (
            TypeError,
            ValueError,
        ):

            messages.error(
                request,
                "Please enter a valid number of seats per row.",
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        if seats_per_row < 1:

            messages.error(
                request,
                "Seats per row must be at least 1.",
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        # ====================================================
        # CONVERT ROW TO NUMBER
        # ====================================================

        def row_to_number(row):

            number = 0

            for character in row:

                number = (
                    number * 26
                    + (
                        ord(character)
                        - ord("A")
                        + 1
                    )
                )

            return number


        def number_to_row(number):

            result = ""

            while number:

                number, remainder = divmod(
                    number - 1,
                    26,
                )

                result = (
                    chr(
                        ord("A")
                        + remainder
                    )
                    + result
                )

            return result


        start_number = row_to_number(
            start_row,
        )

        end_number = row_to_number(
            end_row,
        )


        # ====================================================
        # VALIDATE RANGE
        # ====================================================

        if start_number > end_number:

            messages.error(
                request,
                "Starting row must come before the ending row.",
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        # ====================================================
        # LIMIT GENERATION
        # ====================================================

        total_rows = (
            end_number
            - start_number
            + 1
        )

        total_seats = (
            total_rows
            * seats_per_row
        )

        if total_seats > 1000:

            messages.error(
                request,
                "You cannot generate more than 1,000 seats at once.",
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        # ====================================================
        # CHECK SCREEN CAPACITY
        # ====================================================

        current_seat_count = screen.seats.count()

        new_seat_count = (
            current_seat_count
            + total_seats
        )

        if new_seat_count > screen.capacity:

            remaining_capacity = (
                screen.capacity
                - current_seat_count
            )

            messages.error(
                request,
                (
                    f"This screen has only "
                    f"{remaining_capacity} remaining seat "
                    f"spaces."
                ),
            )

            return redirect(
                "cinemas:generate_seats",
                screen_id=screen.id,
            )


        # ====================================================
        # EXISTING SEATS
        # ====================================================

        existing_seats = set(
            screen.seats.values_list(
                "row",
                "number",
            )
        )


        seats_to_create = []


        # ====================================================
        # BUILD SEATS
        # ====================================================

        for row_number in range(
            start_number,
            end_number + 1,
        ):

            row = number_to_row(
                row_number,
            )

            for seat_number in range(
                1,
                seats_per_row + 1,
            ):

                if (
                    row,
                    seat_number,
                ) in existing_seats:

                    continue

                seats_to_create.append(
                    Seat(
                        screen=screen,
                        row=row,
                        number=seat_number,
                        is_active=True,
                    )
                )


        # ====================================================
        # SAVE
        # ====================================================

        if seats_to_create:

            try:

                with transaction.atomic():

                    Seat.objects.bulk_create(
                        seats_to_create,
                    )

                messages.success(
                    request,
                    (
                        f"{len(seats_to_create)} seats "
                        f"were generated successfully."
                    ),
                )

            except IntegrityError:

                messages.error(
                    request,
                    (
                        "Some seats could not be generated "
                        "because they already exist."
                    ),
                )

        else:

            messages.info(
                request,
                "All requested seats already exist.",
            )


        return redirect(
            "cinemas:seat_list",
            screen_id=screen.id,
        )


    return render(
        request,
        "cinemas/generate_seats.html",
        {
            "screen": screen,
        },
    )