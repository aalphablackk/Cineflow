from django.core.management.base import BaseCommand

from movies.models import Movie


class Command(BaseCommand):

    help = (
        "Backfill trailer_url on the originally-seeded CineFlow movies "
        "with working YouTube links. Only touches trailer_url — every "
        "other field (title, poster, dates, etc.) is left exactly as is."
    )

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Updating trailer_url for existing CineFlow movies..."
            )
        )

        # =====================================================
        # TRAILER URLS TO BACKFILL
        # =====================================================
        #
        # Keyed by slug so this only ever touches movies that were
        # created by the original seed command.
        #
        # Each link below was verified as the real, official trailer
        # for that movie before being added here.
        #
        # =====================================================

        trailer_urls = {
            "avengers-endgame": "https://www.youtube.com/watch?v=TcMBFSGVi1c",
            "john-wick-chapter-4": "https://www.youtube.com/watch?v=qEVUtrk8_B4",
            "black-panther-wakanda-forever": "https://www.youtube.com/watch?v=_Z3QKkl1WyM",
            "guardians-of-the-galaxy-vol-3": "https://www.youtube.com/watch?v=u3V5KDHRQvk",
            "the-matrix": "https://www.youtube.com/watch?v=m8e-FF8MsqU",
            "gladiator": "https://www.youtube.com/watch?v=uvbavW31adA",
            "the-dark-knight": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
            "mission-impossible-dead-reckoning": "https://www.youtube.com/watch?v=avz06PDqDbM",
            "the-hunger-games-catching-fire": "https://www.youtube.com/watch?v=MkvUNfySGQU",
            "a-quiet-place": "https://www.youtube.com/watch?v=WR7cc5t7tv8",
        }

        # =====================================================
        # APPLY UPDATES
        # =====================================================

        updated_count = 0

        missing_count = 0

        for slug, trailer_url in trailer_urls.items():

            movie = Movie.objects.filter(
                slug=slug
            ).first()

            # ================================================
            # MOVIE NOT FOUND
            # ================================================

            if not movie:

                missing_count += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ No movie found with slug: {slug}"
                    )
                )

                continue

            # ================================================
            # UPDATE ONLY trailer_url
            # ================================================

            movie.trailer_url = trailer_url

            movie.save(update_fields=["trailer_url"])

            updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Updated trailer for: {movie.title}"
                )
            )

        # =====================================================
        # SUMMARY
        # =====================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Trailer update completed."
            )
        )

        self.stdout.write(
            f"Trailers updated: {updated_count}"
        )

        self.stdout.write(
            f"Slugs not found: {missing_count}"
        )