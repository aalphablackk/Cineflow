from django.contrib import admin

from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "status",
        "release_date",
        "duration",
        "age_rating",
        "has_poster",
        "created_at",
    )

    list_filter = (
        "status",
        "age_rating",
        "release_date",
    )

    search_fields = (
        "title",
        "slug",
        "description",
    )

    ordering = (
        "-release_date",
        "title",
    )

    prepopulated_fields = {
        "slug": (
            "title",
        ),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Movie Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "duration",
                    "release_date",
                    "age_rating",
                    "status",
                ),
            },
        ),

        (
            "Poster",
            {
                "fields": (
                    "poster",
                    "poster_url",
                ),
            },
        ),

        (
            "Trailer",
            {
                "fields": (
                    "trailer_url",
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

    def has_poster(self, obj):

        return bool(
            obj.poster
            or obj.poster_url
        )

    has_poster.boolean = True
    has_poster.short_description = "Poster"