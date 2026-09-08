import base64
from email.mime.image import MIMEImage
from io import BytesIO

import qrcode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def generate_ticket_qr(ticket):
    """
    Generate a QR code containing the ticket's unique code.
    """

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

    buffer = BytesIO()

    qr_image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def send_ticket_confirmation_email(ticket):
    """
    Send a digital ticket confirmation email.

    The QR code is attached as an inline image so that
    email clients can display it without relying on
    external image hosting.
    """

    booking = ticket.booking
    showtime = booking.showtime
    movie = showtime.movie
    screen = showtime.screen
    cinema = screen.cinema
    user = booking.user

    customer_name = (
        user.get_full_name()
        or user.username
        or "Customer"
    )

    subject = (
        f"CineFlow Ticket Confirmation - "
        f"{ticket.ticket_number}"
    )

    context = {
        "ticket": ticket,
        "booking": booking,
        "showtime": showtime,
        "movie": movie,
        "screen": screen,
        "cinema": cinema,
        "customer": user,
        "customer_name": customer_name,
    }

    text_content = render_to_string(
        "notifications/ticket_confirmation.txt",
        context,
    )

    html_content = render_to_string(
        "notifications/ticket_confirmation.html",
        context,
    )

    qr_bytes = generate_ticket_qr(ticket)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(
        html_content,
        "text/html",
    )

    qr_image = MIMEImage(
        qr_bytes,
        _subtype="png",
    )

    qr_image.add_header(
        "Content-ID",
        "<ticket_qr>",
    )

    qr_image.add_header(
        "Content-Disposition",
        "inline",
        filename="cineflow-ticket-qr.png",
    )

    email.attach(
        qr_image,
    )

    email.send(
        fail_silently=False,
    )

def send_booking_cancellation_email(booking, refund=None):
    """
    Send a booking cancellation and refund status email.
    """

    showtime = booking.showtime
    movie = showtime.movie
    screen = showtime.screen
    cinema = screen.cinema
    user = booking.user

    customer_name = (
        user.get_full_name()
        or user.username
        or "Customer"
    )

    refund_status = None

    if refund:
        refund_status = refund.get_status_display()

    subject = (
        f"CineFlow Booking Cancelled - "
        f"{booking.booking_reference}"
    )

    context = {
        "booking": booking,
        "showtime": showtime,
        "movie": movie,
        "screen": screen,
        "cinema": cinema,
        "customer": user,
        "customer_name": customer_name,
        "refund": refund,
        "refund_status": refund_status,
    }

    text_content = render_to_string(
        "notifications/booking_cancellation.txt",
        context,
    )

    html_content = render_to_string(
        "notifications/booking_cancellation.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(
        html_content,
        "text/html",
    )

    email.send(
        fail_silently=False,
    )
def send_refund_status_email(refund):
    """
    Send an email to the customer when the refund status changes.
    """

    payment = refund.payment
    booking = payment.booking

    showtime = booking.showtime
    movie = showtime.movie
    screen = showtime.screen
    cinema = screen.cinema
    user = booking.user

    customer_name = (
        user.get_full_name()
        or user.username
        or "Customer"
    )

    subject = (
        f"CineFlow Refund Update - "
        f"{booking.booking_reference}"
    )

    context = {
        "refund": refund,
        "payment": payment,
        "booking": booking,
        "showtime": showtime,
        "movie": movie,
        "screen": screen,
        "cinema": cinema,
        "customer": user,
        "customer_name": customer_name,
    }

    text_content = render_to_string(
        "notifications/refund_status.txt",
        context,
    )

    html_content = render_to_string(
        "notifications/refund_status.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(
        html_content,
        "text/html",
    )

    email.send(
        fail_silently=False,
    )