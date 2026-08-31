from django.urls import path

from . import views


app_name = "cinemas"


urlpatterns = [

    # ========================================================
    # CINEMA MANAGEMENT
    # ========================================================

    path(
        "create/",
        views.create_cinema,
        name="create_cinema",
    ),

    path(
        "<int:cinema_id>/edit/",
        views.edit_cinema,
        name="edit_cinema",
    ),

    path(
        "<int:cinema_id>/delete/",
        views.delete_cinema,
        name="delete_cinema",
    ),


    # ========================================================
    # SCREEN MANAGEMENT
    # ========================================================

    path(
        "screens/create/",
        views.create_screen,
        name="create_screen",
    ),

    path(
        "screens/<int:screen_id>/edit/",
        views.edit_screen,
        name="edit_screen",
    ),

    path(
        "screens/<int:screen_id>/delete/",
        views.delete_screen,
        name="delete_screen",
    ),


    # ========================================================
    # SEAT MANAGEMENT
    # ========================================================

    path(
        "screens/<int:screen_id>/seats/",
        views.seat_list,
        name="seat_list",
    ),

    path(
        "screens/<int:screen_id>/seats/create/",
        views.create_seat,
        name="create_seat",
    ),

    path(
        "screens/<int:screen_id>/seats/generate/",
        views.generate_seats,
        name="generate_seats",
    ),

    path(
        "seats/<int:seat_id>/edit/",
        views.edit_seat,
        name="edit_seat",
    ),

    path(
        "seats/<int:seat_id>/delete/",
        views.delete_seat,
        name="delete_seat",
    ),


    # ========================================================
    # CUSTOMER PAGES
    # ========================================================

    path(
        "",
        views.cinema_list,
        name="cinema_list",
    ),

    path(
        "<slug:slug>/",
        views.cinema_detail,
        name="cinema_detail",
    ),

]