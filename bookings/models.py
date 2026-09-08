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

        # constraints = [
        # models.UniqueConstraint(
        #     fields=["showtime", "seat"],
        #     name="unique_seat_per_showtime",
        # ),
        # ]

    def __str__(self):
        return (
            f"{self.booking.booking_reference} - "
            f"{self.seat.label}"
        )

class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    class Provider(models.TextChoices):
        TEST = "test", "Test Payment"
        PAYSTACK = "paystack", "Paystack"

    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    payment_reference = models.CharField(
        max_length=100,
        unique=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.TEST,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.payment_reference


class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        NEEDS_ATTENTION = "needs-attention", "Needs Attention"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="refund",
    )

    refund_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    reason = models.TextField(
        blank=True,
    )

    customer_note = models.TextField(
        blank=True,
    )

    merchant_note = models.TextField(
        blank=True,
    )

    paystack_transaction = models.CharField(
        max_length=255,
        blank=True,
    )

    expected_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failure_reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"Refund for "
            f"{self.payment.payment_reference}"
        )


class SeatReservation(models.Model):
    """
    Represents the current active reservation of a seat
    for a specific showtime.

    This is separate from BookingSeat so that historical
    booking-seat records are preserved after cancellation
    or expiration.
    """

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="seat_reservations",
    )

    showtime = models.ForeignKey(
        Showtime,
        on_delete=models.PROTECT,
        related_name="seat_reservations",
    )

    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="seat_reservations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["showtime", "seat"],
                name="unique_active_seat_per_showtime",
            ),
        ]

    def __str__(self):
        return (
            f"{self.showtime} - "
            f"{self.seat} - "
            f"{self.booking.booking_reference}"
        )