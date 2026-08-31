from django.urls import path

from . import views


app_name = "staff"


urlpatterns = [

    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),


    # ========================================================
    # MOVIES
    # ========================================================

    path(
        "movies/",
        views.movies,
        name="movies",
    ),

    path(
        "movies/create/",
        views.movie_create,
        name="movie_create",
    ),

    path(
        "movies/<int:pk>/edit/",
        views.movie_edit,
        name="movie_edit",
    ),

    path(
        "movies/<int:pk>/delete/",
        views.movie_delete,
        name="movie_delete",
    ),


    # ========================================================
    # CINEMAS
    # ========================================================

    path(
        "cinemas/",
        views.cinemas,
        name="cinemas",
    ),

    path(
        "cinemas/create/",
        views.cinema_create,
        name="cinema_create",
    ),

    path(
        "cinemas/<int:pk>/edit/",
        views.cinema_edit,
        name="cinema_edit",
    ),

    path(
        "cinemas/<int:pk>/delete/",
        views.cinema_delete,
        name="cinema_delete",
    ),


    # ========================================================
    # SCREEN MANAGEMENT
    # ========================================================

    path(
        "cinemas/<int:cinema_id>/screens/",
        views.screens,
        name="screens",
    ),

    path(
        "cinemas/<int:cinema_id>/screens/create/",
        views.screen_create,
        name="screen_create",
    ),

    path(
        "screens/<int:pk>/edit/",
        views.screen_edit,
        name="screen_edit",
    ),

    path(
        "screens/<int:pk>/delete/",
        views.screen_delete,
        name="screen_delete",
    ),

    # ========================================================
    # SEAT MANAGEMENT
    # ========================================================

    path(
        "screens/<int:screen_id>/seats/",
        views.seats,
        name="seats",
    ),

    path(
        "screens/<int:screen_id>/seats/create/",
        views.seat_create,
        name="seat_create",
    ),

    path(
        "seats/<int:pk>/edit/",
        views.seat_edit,
        name="seat_edit",
    ),

    path(
        "seats/<int:pk>/delete/",
        views.seat_delete,
        name="seat_delete",
    ),
    path(
    "screens/<int:screen_id>/seats/generate/",
    views.generate_seats,
    name="generate_seats",
    ),
    # ========================================================
    # SHOWTIMES
    # ========================================================

    path(
        "showtimes/",
        views.showtimes,
        name="showtimes",
    ),

    path(
        "showtimes/create/",
        views.showtime_create,
        name="showtime_create",
    ),

    path(
        "showtimes/<int:pk>/edit/",
        views.showtime_edit,
        name="showtime_edit",
    ),

    path(
        "showtimes/<int:pk>/cancel/",
        views.showtime_cancel,
        name="showtime_cancel",
    ),

    path(
        "showtimes/<int:pk>/delete/",
        views.showtime_delete,
        name="showtime_delete",
    ),

    path(
        "showtimes/cinema/<int:cinema_id>/screens/",
        views.cinema_screens,
        name="cinema_screens",
    ),
    # ========================================================
    # BOOKINGS
    # ========================================================

    path(
        "bookings/",
        views.bookings,
        name="bookings",
    ),
    # ========================================================
    # SUPPORT
    # ========================================================

    path(
        "support/",
        views.support,
        name="support",
    ),

    path(
        "support/<int:ticket_id>/status/",
        views.support_ticket_status,
        name="support_ticket_status",
    ),

    path(
        "support/<int:ticket_id>/priority/",
        views.support_ticket_priority,
        name="support_ticket_priority",
    ),
]


