from django.contrib import admin

from .models import (
    Cinema,
    Screen,
    Seat,
)


# ============================================================
# SCREEN INLINE
# ============================================================

class ScreenInline(admin.TabularInline):

    model = Screen

    extra = 0

    fields = (
        "name",
        "screen_type",
        "capacity",
        "is_active",
    )

    show_change_link = True


# ============================================================
# SEAT INLINE
# ============================================================

class SeatInline(admin.TabularInline):

    model = Seat

    extra = 0

    fields = (
        "row",
        "number",
        "is_active",
    )

    show_change_link = True


# ============================================================
# CINEMA ADMIN
# ============================================================

@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "city",
        "state",
        "screen_count",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "state",
        "city",
    )

    search_fields = (
        "name",
        "slug",
        "city",
        "state",
        "address",
        "phone",
        "email",
    )

    ordering = (
        "name",
    )

    prepopulated_fields = {
        "slug": (
            "name",
        ),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Cinema Information",
            {
                "fields": (
                    "name",
                    "slug",
                    "is_active",
                ),
            },
        ),

        (
            "Location",
            {
                "fields": (
                    "address",
                    "city",
                    "state",
                ),
            },
        ),

        (
            "Contact",
            {
                "fields": (
                    "phone",
                    "email",
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
        ScreenInline,
    ]

    def screen_count(self, obj):

        return obj.screens.count()

    screen_count.short_description = "Screens"


# ============================================================
# SCREEN ADMIN
# ============================================================

@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "cinema",
        "screen_type",
        "capacity",
        "seat_count",
        "is_active",
        "created_at",
    )

    list_filter = (
        "screen_type",
        "is_active",
        "cinema",
    )

    search_fields = (
        "name",
        "cinema__name",
    )

    ordering = (
        "cinema",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Screen Information",
            {
                "fields": (
                    "cinema",
                    "name",
                    "screen_type",
                    "capacity",
                    "is_active",
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
        SeatInline,
    ]

    def seat_count(self, obj):

        return obj.seats.count()

    seat_count.short_description = "Seats"


# ============================================================
# SEAT ADMIN
# ============================================================

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):

    list_display = (
        "label",
        "screen",
        "cinema_name",
        "row",
        "number",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "screen__cinema",
        "screen",
    )

    search_fields = (
        "row",
        "screen__name",
        "screen__cinema__name",
    )

    ordering = (
        "screen",
        "row",
        "number",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Seat Information",
            {
                "fields": (
                    "screen",
                    "row",
                    "number",
                    "is_active",
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

    def cinema_name(self, obj):

        return obj.screen.cinema.name

    cinema_name.short_description = "Cinema"