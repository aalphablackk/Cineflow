from datetime import datetime, timedelta

from django.db import models

from movies.models import Movie
from cinemas.models import Screen


class Showtime(models.Model):

    class BookingMode(models.TextChoices):
        ASSIGNED = "assigned", "Assigned Seating"
        GENERAL = "general", "General Admission"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="showtimes",
    )

    screen = models.ForeignKey(
        Screen,
        on_delete=models.PROTECT,
        related_name="showtimes",
    )

    show_date = models.DateField()

    start_time = models.TimeField()

    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    booking_mode = models.CharField(
        max_length=20,
        choices=BookingMode.choices,
        default=BookingMode.GENERAL,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def end_time(self):
        start_datetime = datetime.combine(
            self.show_date,
            self.start_time,
        )

        end_datetime = start_datetime + timedelta(
            minutes=self.movie.duration
        )

        return end_datetime.time()

    def __str__(self):
        return (
            f"{self.movie.title} - "
            f"{self.show_date} "
            f"{self.start_time}"
        )