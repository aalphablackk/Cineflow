from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "Create and configure CineFlow staff groups and permissions."

    # ============================================================
    # GROUP PERMISSIONS
    # ============================================================

    GROUP_PERMISSIONS = {

        "Cinema Manager": {

            "cinemas": [
                "cinema",
                "screen",
                "seat",
            ],

        },

        "Movie Manager": {

            "movies": [
                "movie",
            ],

        },

        "Showtime Manager": {

            "showtimes": [
                "showtime",
            ],

        },

        "Booking Manager": {

            "bookings": [
                "booking",
                "bookingseat",
            ],

        },

    }

    # ============================================================
    # COMMAND
    # ============================================================

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Setting up CineFlow staff groups..."
            )
        )

        for group_name, app_models in self.GROUP_PERMISSIONS.items():

            group, created = Group.objects.get_or_create(
                name=group_name
            )

            if created:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created group: {group_name}"
                    )
                )

            else:

                self.stdout.write(
                    f"Group already exists: {group_name}"
                )

            # ----------------------------------------------------
            # Add permissions
            # ----------------------------------------------------

            for app_label, model_names in app_models.items():

                for model_name in model_names:

                    permissions = Permission.objects.filter(
                        content_type__app_label=app_label,
                        content_type__model=model_name,
                        codename__in=[
                            f"view_{model_name}",
                            f"add_{model_name}",
                            f"change_{model_name}",
                        ],
                    )

                    group.permissions.add(
                        *permissions
                    )

                    self.stdout.write(
                        f"  Added permissions for "
                        f"{app_label}.{model_name}"
                    )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "CineFlow staff groups configured successfully."
            )
        )