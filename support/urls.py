from django.urls import path

from . import views


app_name = "support"


urlpatterns = [

    path(
        "",
        views.my_tickets,
        name="my_tickets",
    ),

    path(
        "new/",
        views.create_ticket,
        name="create_ticket",
    ),

    path(
        "booking/<str:booking_reference>/new/",
        views.create_ticket,
        name="create_booking_ticket",
    ),

    path(
        "<int:ticket_id>/",
        views.ticket_detail,
        name="ticket_detail",
    ),

]