from django.contrib import admin

from .models import Showtime


@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):

    list_display = (
        "movie",
        "cinema",
        "screen",
        "show_date",
        "start_time",
        "end_time_display",
        "ticket_price",
        "booking_mode",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "booking_mode",
        "show_date",
        "screen__cinema",
        "screen",
    )

    search_fields = (
        "movie__title",
        "screen__name",
        "screen__cinema__name",
    )

    ordering = (
        "-show_date",
        "start_time",
    )

    readonly_fields = (
        "end_time_display",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Showtime",
            {
                "fields": (
                    "movie",
                    "screen",
                    "show_date",
                    "start_time",
                    "end_time_display",
                ),
            },
        ),

        (
            "Booking",
            {
                "fields": (
                    "ticket_price",
                    "booking_mode",
                    "status",
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

    def cinema(self, obj):

        return obj.screen.cinema.name

    cinema.short_description = "Cinema"

    def end_time_display(self, obj):

        return obj.end_time

    end_time_display.short_description = "End Time"