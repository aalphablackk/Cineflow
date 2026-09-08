from django.urls import path

from . import views


app_name = "tickets"


urlpatterns = [
    path(
        "verify/",
        views.verify_ticket_view,
        name="verify_ticket",
    ),

    path(
        "verify/<str:ticket_code>/use/",
        views.use_ticket_view,
        name="use_ticket",
    ),
    path(
        "<str:ticket_number>/",
        views.ticket_detail,
        name="ticket_detail",
    ),
]