from django.contrib import admin



from .models import SupportMessage, SupportTicket

# Register your models here.

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "subject",
        "customer",
        "booking",
        "status",
        "priority",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "priority",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "subject",
        "customer__username",
        "customer__email",
        "booking__booking_reference",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "customer",
        "booking",
    )

    ordering = (
        "-created_at",
    )


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "ticket",
        "sender",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "message",
        "sender__username",
        "sender__email",
        "ticket__subject",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "ticket",
        "sender",
    )

    ordering = (
        "created_at",
    )