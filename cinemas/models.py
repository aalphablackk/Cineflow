from django.db import models


class Cinema(models.Model):

    name = models.CharField(
        max_length=150
    )

    slug = models.SlugField(
        unique=True
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class Screen(models.Model):

    class ScreenType(models.TextChoices):
        STANDARD = "standard", "Standard"
        VIP = "vip", "VIP"
        IMAX = "imax", "IMAX"

    cinema = models.ForeignKey(
        Cinema,
        on_delete=models.CASCADE,
        related_name="screens"
    )

    name = models.CharField(
        max_length=100
    )

    screen_type = models.CharField(
        max_length=20,
        choices=ScreenType.choices,
        default=ScreenType.STANDARD
    )

    capacity = models.PositiveIntegerField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.cinema.name} - {self.name}"




class Seat(models.Model):

    screen = models.ForeignKey(
        Screen,
        on_delete=models.CASCADE,
        related_name="seats",
    )

    row = models.CharField(
        max_length=5
    )

    number = models.PositiveIntegerField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["screen", "row", "number"],
                name="unique_seat_per_screen",
            ),
        ]

    @property
    def label(self):
        return f"{self.row}{self.number}"

    def __str__(self):
        return f"{self.screen.name} - {self.label}"