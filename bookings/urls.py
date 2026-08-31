from django.urls import path

from . import views


app_name = "bookings"


urlpatterns = [

    path(
        "create/<int:showtime_id>/",
        views.create_booking,
        name="create_booking",
    ),
    path(
        "checkout/<int:booking_id>/",
        views.checkout,
        name="checkout",
    ),

    path(
    "my-bookings/",
    views.my_bookings,
    name="my_bookings",
    ),
    path(
        "<str:booking_reference>/",
        views.booking_detail,
        name="booking_detail",
    ),

]