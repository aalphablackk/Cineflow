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
        "payment/<str:payment_reference>/",
        views.test_payment,
        name="test_payment",
    ),

    path(
        "payment/<int:booking_id>/initialize/",
        views.initialize_payment,
        name="initialize_payment",
    ),
    path(
        "payment/<str:payment_reference>/success/",
        views.simulate_successful_payment,
        name="simulate_successful_payment",
    ),
    path(
    "payment/paystack/callback/",
    views.paystack_callback,
    name="paystack_callback",
    ),
    path(
    "payment/paystack/webhook/",
    views.paystack_webhook,
    name="paystack_webhook",
    ),
    path(
        "payment/<str:payment_reference>/failed/",
        views.simulate_failed_payment,
        name="simulate_failed_payment",
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
    path(
    "<str:booking_reference>/cancel/",
    views.cancel_booking_view,
    name="cancel_booking",
),

]