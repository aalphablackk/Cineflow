from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

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

    # ========================================================
    # SHOWTIME DATETIME HELPERS
    # ========================================================

    @property
    def start_datetime(self):
        """
        Return the full timezone-aware datetime
        when the show starts.
        """

        naive_datetime = datetime.combine(
            self.show_date,
            self.start_time,
        )

        return timezone.make_aware(
            naive_datetime,
            timezone.get_current_timezone(),
        )

    @property
    def end_datetime(self):
        """
        Return the full timezone-aware datetime
        when the movie finishes.
        """

        return self.start_datetime + timedelta(
            minutes=self.movie.duration
        )

    @property
    def end_time(self):
        """
        Return only the ending time.

        Kept for compatibility with existing code.
        """

        return self.end_datetime.time()

    # ========================================================
    # SHOWTIME STATUS
    # ========================================================

    @property
    def has_started(self):
        """
        True once the movie start time has been reached.
        """

        return timezone.now() >= self.start_datetime

    @property
    def has_finished(self):
        """
        True once the movie duration has completely elapsed.
        """

        return timezone.now() >= self.end_datetime

    @property
    def is_bookable(self):
        """
        A showtime is bookable only when:

        - It is scheduled
        - It has not started
        - It has not finished
        """

        return (
            self.status == self.Status.SCHEDULED
            and not self.has_started
            and not self.has_finished
        )

    @property
    def display_status(self):
        """
        Return the real-time status that should be
        displayed to customers/staff.

        Database status remains unchanged until
        explicitly updated.
        """

        if self.status == self.Status.CANCELLED:
            return self.Status.CANCELLED

        if self.has_finished:
            return self.Status.COMPLETED

        if self.has_started:
            return "showing"

        return self.Status.SCHEDULED

    # ========================================================
    # DATABASE STATUS SYNCHRONIZATION
    # ========================================================

    def update_status_if_finished(self):
        """
        Persist COMPLETED status once the movie has finished.

        Returns True if the database status was changed.
        """

        if (
            self.status == self.Status.SCHEDULED
            and self.has_finished
        ):
            self.status = self.Status.COMPLETED

            self.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

            return True

        return False

    def __str__(self):
        return (
            f"{self.movie.title} - "
            f"{self.show_date} "
            f"{self.start_time}"
        )