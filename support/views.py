
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from bookings.models import Booking

from .forms import SupportTicketForm,SupportReplyForm
from .models import SupportMessage, SupportTicket

# Create your views here.

# ============================================================
# CREATE SUPPORT TICKET
# ============================================================

@login_required
def create_ticket(
    request,
    booking_reference=None,
):

    booking = None

    # --------------------------------------------------------
    # OPTIONAL BOOKING
    # --------------------------------------------------------

    if booking_reference:

        booking = get_object_or_404(
            Booking,
            booking_reference=booking_reference,
            user=request.user,
        )

    # --------------------------------------------------------
    # HANDLE FORM
    # --------------------------------------------------------

    if request.method == "POST":

        form = SupportTicketForm(
            request.POST,
        )

        if form.is_valid():

            ticket = form.save(
                commit=False
            )

            ticket.customer = request.user
            ticket.booking = booking

            ticket.save()

            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=form.cleaned_data[
                    "message"
                ],
            )

            messages.success(
                request,
                "Your support request has been submitted.",
            )

            return redirect(
                "support:ticket_detail",
                ticket_id=ticket.id,
            )

    else:

        form = SupportTicketForm()

    return render(
        request,
        "support/create_ticket.html",
        {
            "form": form,
            "booking": booking,
        },
    )


# ============================================================
# CUSTOMER TICKET DETAIL
# ============================================================

@login_required
def ticket_detail(request, ticket_id):

    ticket = get_object_or_404(
        SupportTicket.objects.prefetch_related(
            "messages__sender",
        ),
        id=ticket_id,
        customer=request.user,
    )

    can_reply = (
        ticket.status != SupportTicket.Status.CLOSED
    )

    if request.method == "POST":

        if not can_reply:

            messages.error(
                request,
                "This support request has been closed. "
                "Please create a new support request if "
                "you need further assistance.",
            )

            return redirect(
                "support:ticket_detail",
                ticket_id=ticket.id,
            )

        form = SupportReplyForm(
            request.POST
        )

        if form.is_valid():

            support_message = form.save(
                commit=False
            )

            support_message.ticket = ticket
            support_message.sender = request.user

            support_message.save()

            # Reopen the conversation when the customer replies
            if ticket.status in [
                SupportTicket.Status.RESOLVED,
                SupportTicket.Status.WAITING_FOR_CUSTOMER,
            ]:

                ticket.status = (
                    SupportTicket.Status.OPEN
                )

                ticket.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            messages.success(
                request,
                "Your reply has been sent.",
            )

            return redirect(
                "support:ticket_detail",
                ticket_id=ticket.id,
            )

    else:

        form = SupportReplyForm()

    return render(
        request,
        "support/ticket_detail.html",
        {
            "ticket": ticket,
            "form": form,
            "can_reply": can_reply,
        },
    )

# ============================================================
# CUSTOMER TICKET LIST
# ============================================================

@login_required
def my_tickets(request):

    tickets = (
        SupportTicket.objects
        .filter(
            customer=request.user,
        )
        .select_related(
            "booking",
            "booking__showtime",
            "booking__showtime__movie",
        )
        .order_by(
            "-updated_at",
        )
    )

    return render(
        request,
        "support/my_tickets.html",
        {
            "tickets": tickets,
        },
    )