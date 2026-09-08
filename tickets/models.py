from django.db import models

# Create your models here.
import secrets


from bookings.models import Booking


class Ticket(models.Model):

    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name="ticket",
    )

    ticket_number = models.CharField(
        max_length=30,
        unique=True,
    )

    ticket_code = models.CharField(
        max_length=40,
        unique=True,
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_valid = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    used_at = models.DateTimeField(
    null=True,
    blank=True,
    )
    
    def __str__(self):
        return self.ticket_number