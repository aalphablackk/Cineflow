from django.db import models

from django.contrib.auth.models import User


from bookings.models import Booking

# Create your models here.

class SupportTicket(models.Model):

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        WAITING_FOR_CUSTOMER = (
            "waiting_for_customer",
            "Waiting for Customer",
        )
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="support_tickets",
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="support_tickets",
        null=True,
        blank=True,
    )

    subject = models.CharField(
        max_length=200,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        return (
            f"#{self.id} - "
            f"{self.subject}"
        )


class SupportMessage(models.Model):

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="support_messages",
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "created_at",
        ]

    def __str__(self):

        return (
            f"Message #{self.id} "
            f"on Ticket #{self.ticket.id}"
        )

