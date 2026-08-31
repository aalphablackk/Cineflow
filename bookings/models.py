from django.contrib.auth.models import User
from django.db import models

from showtimes.models import Showtime
from cinemas.models import Seat


class Booking(models.Model):

    class Status(models.TextChoices):
        HELD = "held", "Held"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    showtime = models.ForeignKey(
        Showtime,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    booking_reference = models.CharField(
        max_length=20,
        unique=True,
    )

    ticket_quantity = models.PositiveIntegerField()

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.HELD,
    )

    hold_expires_at = models.DateTimeField(
    null=True,
    blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.booking_reference


class BookingSeat(models.Model):

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="booking_seats",
    )

    showtime = models.ForeignKey(
        Showtime,
        on_delete=models.PROTECT,
        related_name="booking_seats",
    )

    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="booking_seats",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=["showtime", "seat"],
    #             name="unique_seat_per_showtime",
    #         ),
    #     ]
    class Meta:
        ordering = ["seat"]

        constraints = [
        models.UniqueConstraint(
            fields=["showtime", "seat"],
            name="unique_seat_per_showtime",
        ),
        ]

    def __str__(self):
        return (
            f"{self.booking.booking_reference} - "
            f"{self.seat.label}"
        )