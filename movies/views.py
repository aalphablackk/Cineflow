from django.db.models import (
    F,
    OuterRef,
    Q,
    Subquery,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.utils import timezone

from bookings.services import (
    get_available_capacity,
    get_available_seats,
)
from showtimes.models import Showtime

from .models import Movie

from django.core.paginator import Paginator


def home(request):

    today = timezone.localdate()
    current_time = timezone.localtime().time()

    upcoming_showtimes = Showtime.objects.filter(
        movie=OuterRef("pk"),
        status=Showtime.Status.SCHEDULED,
    ).filter(
        Q(show_date__gt=today)
        |
        Q(
            show_date=today,
            start_time__gte=current_time,
        )
    ).order_by(
        "show_date",
        "start_time",
    )

    movies = Movie.objects.filter(
        status=Movie.Status.NOW_SHOWING,
    ).annotate(
        next_show_date=Subquery(
            upcoming_showtimes.values(
                "show_date"
            )[:1]
        ),
        next_show_time=Subquery(
            upcoming_showtimes.values(
                "start_time"
            )[:1]
        ),
    ).order_by(
        F("next_show_date").asc(nulls_last=True),
        F("next_show_time").asc(nulls_last=True),
        "-release_date",
        "title",
    )[:4]

    return render(
        request,
        "home.html",
        {
            "movies": movies,
        },
    )

def movie_list(request):

    query = request.GET.get(
        "q",
        "",
    ).strip()

    # ---------------------------------------------------------
    # CURRENT DATE AND TIME
    # ---------------------------------------------------------

    today = timezone.localdate()
    current_time = timezone.localtime().time()

    # ---------------------------------------------------------
    # UPCOMING SHOWTIMES
    # ---------------------------------------------------------

    upcoming_showtimes = Showtime.objects.filter(
        movie=OuterRef("pk"),
        status=Showtime.Status.SCHEDULED,
    ).filter(
        Q(show_date__gt=today)
        |
        Q(
            show_date=today,
            start_time__gte=current_time,
        )
    ).order_by(
        "show_date",
        "start_time",
    )

    # ---------------------------------------------------------
    # MOVIES
    # ---------------------------------------------------------

    movies = Movie.objects.filter(
        status=Movie.Status.NOW_SHOWING,
    )

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    if query:

        movies = movies.filter(
            Q(title__icontains=query)
            |
            Q(description__icontains=query)
        )

    # ---------------------------------------------------------
    # NEXT SHOWTIME
    # ---------------------------------------------------------

    movies = movies.annotate(
        next_show_date=Subquery(
            upcoming_showtimes.values(
                "show_date"
            )[:1]
        ),
        next_show_time=Subquery(
            upcoming_showtimes.values(
                "start_time"
            )[:1]
        ),
    ).order_by(
        F("next_show_date").asc(
            nulls_last=True
        ),
        F("next_show_time").asc(
            nulls_last=True
        ),
        "-release_date",
        "title",
    )
    paginator = Paginator(movies, 12)

    page_number = request.GET.get("page")

    movies = paginator.get_page(page_number)

    return render(
        request,
        "movies/movie_list.html",
        {
            "movies": movies,
            "query": query,
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
        movie.showtimes
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

        if showtime.booking_mode == Showtime.BookingMode.ASSIGNED:

            showtime.available_count = (
                get_available_seats(showtime).count()
            )

            showtime.availability_label = "seats"

        else:

            showtime.available_count = (
                get_available_capacity(showtime)
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