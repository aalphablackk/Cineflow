from django.contrib import admin

from .models import Booking, BookingSeat


# ============================================================
# BOOKING SEAT INLINE
# ============================================================

class BookingSeatInline(admin.TabularInline):

    model = BookingSeat

    extra = 0

    fields = (
        "seat",
        "showtime",
        "price",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    show_change_link = True


# ============================================================
# BOOKING ADMIN
# ============================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "booking_reference",
        "user",
        "movie",
        "cinema",
        "showtime_date",
        "showtime_time",
        "ticket_quantity",
        "total_amount",
        "status",
        "hold_expires_at",
        "created_at",
    )

    list_filter = (
        "status",
        "showtime__booking_mode",
        "showtime__screen__cinema",
        "showtime__show_date",
        "created_at",
    )

    search_fields = (
        "booking_reference",
        "user__username",
        "user__email",
        "showtime__movie__title",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "booking_reference",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Booking",
            {
                "fields": (
                    "booking_reference",
                    "user",
                    "showtime",
                    "ticket_quantity",
                    "total_amount",
                    "status",
                ),
            },
        ),

        (
            "Hold Information",
            {
                "fields": (
                    "hold_expires_at",
                ),
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),

    )

    inlines = [
        BookingSeatInline,
    ]

    def movie(self, obj):

        return obj.showtime.movie.title

    movie.short_description = "Movie"

    def cinema(self, obj):

        return obj.showtime.screen.cinema.name

    cinema.short_description = "Cinema"

    def showtime_date(self, obj):

        return obj.showtime.show_date

    showtime_date.short_description = "Date"

    def showtime_time(self, obj):

        return obj.showtime.start_time

    showtime_time.short_description = "Time"


# ============================================================
# BOOKING SEAT ADMIN
# ============================================================

@admin.register(BookingSeat)
class BookingSeatAdmin(admin.ModelAdmin):

    list_display = (
        "booking",
        "showtime",
        "seat",
        "price",
        "created_at",
    )

    list_filter = (
        "showtime__show_date",
        "showtime__screen__cinema",
        "showtime",
    )

    search_fields = (
        "booking__booking_reference",
        "booking__user__username",
        "seat__row",
        "seat__screen__name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )