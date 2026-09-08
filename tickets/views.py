from django.contrib import messages
from staff.decorators import staff_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .forms import TicketVerificationForm
from .models import Ticket
from .services import use_ticket, verify_ticket
import base64
from io import BytesIO

import qrcode

@login_required
def ticket_detail(request, ticket_number):

    ticket = get_object_or_404(
        Ticket.objects.select_related(
            "booking",
            "booking__user",
            "booking__showtime",
            "booking__showtime__movie",
            "booking__showtime__screen",
            "booking__showtime__screen__cinema",
        ).prefetch_related(
            "booking__booking_seats__seat",
            "booking__payments",
        ),
        ticket_number=ticket_number,
        booking__user=request.user,
    )


    # ============================================================
    # GENERATE REAL QR CODE
    # ============================================================

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )

    qr.add_data(ticket.ticket_code)

    qr.make(
        fit=True
    )

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white",
    )


    # ============================================================
    # CONVERT QR IMAGE TO BASE64
    # ============================================================

    buffer = BytesIO()

    qr_image.save(
        buffer,
        format="PNG",
    )

    qr_code = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


    return render(
        request,
        "tickets/ticket_detail.html",
        {
            "ticket": ticket,
            "qr_code": qr_code,
        },
    )

@staff_required
def verify_ticket_view(request):
    """
    Allow authorized staff to verify a ticket code.
    """

    form = TicketVerificationForm()
    ticket = None
    verification_error = None

    if request.method == "POST":

        form = TicketVerificationForm(request.POST)

        if form.is_valid():

            ticket_code = form.cleaned_data["ticket_code"]

            try:

                ticket = verify_ticket(
                    ticket_code
                )

            except ValidationError as exc:

                verification_error = exc.messages[0]

    return render(
        request,
        "tickets/verify_ticket.html",
        {
            "form": form,
            "ticket": ticket,
            "verification_error": verification_error,
        },
    )


@staff_required
def use_ticket_view(request, ticket_code):
    """
    Admit a customer by consuming their ticket.
    """

    if request.method != "POST":
        return redirect("tickets:verify_ticket")

    try:

        ticket = use_ticket(
            ticket_code
        )

    except ValidationError as exc:

        messages.error(
            request,
            exc.messages[0],
        )

        return redirect(
            "tickets:verify_ticket"
        )

    messages.success(
        request,
        "Ticket verified successfully. Customer admitted.",
    )

    return redirect(
        "tickets:verify_ticket"
    )