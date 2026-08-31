from django.shortcuts import (
    get_object_or_404,
    render,
)

from bookings.services import (
    get_available_capacity,
    get_available_seats,
)
from showtimes.models import Showtime

from .models import Movie


def home(request):

    movies = Movie.objects.filter(
        status=Movie.Status.NOW_SHOWING,
    ).order_by(
        "release_date",
    )[:4]

    return render(
        request,
        "home.html",
        {
            "movies": movies,
        },
    )


def movie_list(request):

    movies = Movie.objects.filter(
        status=Movie.Status.NOW_SHOWING,
    ).order_by(
        "-release_date",
    )

    return render(
        request,
        "movies/movie_list.html",
        {
            "movies": movies,
        },
    )


def movie_detail(request, slug):

    movie = get_object_or_404(
        Movie.objects.prefetch_related(
            "showtimes",
            "showtimes__screen",
            "showtimes__screen__cinema",
        ),
        slug=slug,
    )

    showtimes = (
        movie.showtimes.filter(
            status=Showtime.Status.SCHEDULED,
        )
        .select_related(
            "screen",
            "screen__cinema",
        )
        .order_by(
            "show_date",
            "start_time",
        )
    )

    for showtime in showtimes:

        if (
            showtime.booking_mode
            == Showtime.BookingMode.ASSIGNED
        ):

            showtime.available_count = (
                get_available_seats(
                    showtime
                ).count()
            )

            showtime.availability_label = "seats"

        else:

            showtime.available_count = (
                get_available_capacity(
                    showtime
                )
            )

            showtime.availability_label = "tickets"

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "showtimes": showtimes,
        },
    )