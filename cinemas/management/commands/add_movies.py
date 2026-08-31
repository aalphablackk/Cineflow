from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Movie


class Command(BaseCommand):

    help = "Add additional development movies to CineFlow."

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Adding CineFlow development movies..."
            )
        )


        # =====================================================
        # MOVIES TO ADD
        # =====================================================
        #
        # Add new movies inside this list.
        #
        # Existing movies will NOT be updated.
        #
        # A movie is identified by its unique slug.
        #
        # =====================================================

        movies = [

            # =================================================
            # MOVIE 1
            # =================================================

            {
                "slug": "avengers-endgame",

                "title": "Avengers: Endgame",

                "description": (
                    "After the devastating events caused by Thanos, "
                    "the remaining Avengers must find a way to restore "
                    "what was lost and face one final battle."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg"
                ),

                "trailer_url": "",

                "duration": 181,

                "release_date": date(2019, 4, 26),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 2
            # =================================================

            {
                "slug": "john-wick-chapter-4",

                "title": "John Wick: Chapter 4",

                "description": (
                    "John Wick uncovers a path to defeating the High Table, "
                    "but before he can earn his freedom, he must face a "
                    "powerful new enemy and his deadly allies."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/vZloFAK7NmvMGKE7VkF5UHaz0I.jpg"
                ),

                "trailer_url": "",

                "duration": 169,

                "release_date": date(2023, 3, 24),

                "age_rating": "R",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 3
            # =================================================

            {
                "slug": "black-panther-wakanda-forever",

                "title": "Black Panther: Wakanda Forever",

                "description": (
                    "The people of Wakanda fight to protect their nation "
                    "from powerful forces following the death of King T'Challa."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/sv1xJUazXeYqALzczSZ3O6nkH75.jpg"
                ),

                "trailer_url": "",

                "duration": 161,

                "release_date": date(2022, 11, 11),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 4
            # =================================================

            {
                "slug": "guardians-of-the-galaxy-vol-3",

                "title": "Guardians of the Galaxy Vol. 3",

                "description": (
                    "The Guardians embark on a dangerous mission to save "
                    "one of their own while confronting the events of their past."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/r2J02Z2OpNTctfOSN1Ydgii51I3.jpg"
                ),

                "trailer_url": "",

                "duration": 150,

                "release_date": date(2023, 5, 5),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 5
            # =================================================

            {
                "slug": "the-matrix",

                "title": "The Matrix",

                "description": (
                    "A computer programmer discovers that reality is "
                    "far different from what he believed and joins a "
                    "rebellion against the machines controlling humanity."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg"
                ),

                "trailer_url": "",

                "duration": 136,

                "release_date": date(1999, 3, 31),

                "age_rating": "R",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 6
            # =================================================

            {
                "slug": "gladiator",

                "title": "Gladiator",

                "description": (
                    "A betrayed Roman general is forced into slavery and "
                    "must fight as a gladiator while seeking justice."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg"
                ),

                "trailer_url": "",

                "duration": 155,

                "release_date": date(2000, 5, 5),

                "age_rating": "R",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 7
            # =================================================

            {
                "slug": "the-dark-knight",

                "title": "The Dark Knight",

                "description": (
                    "Batman faces a criminal mastermind whose actions "
                    "push Gotham City into chaos and test the limits "
                    "of the city's defenders."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
                ),

                "trailer_url": "",

                "duration": 152,

                "release_date": date(2008, 7, 18),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 8
            # =================================================

            {
                "slug": "mission-impossible-dead-reckoning",

                "title": "Mission: Impossible - Dead Reckoning",

                "description": (
                    "Ethan Hunt and his team race to prevent a powerful "
                    "new weapon from falling into the wrong hands."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/NNxYkU70HPurnNzbCjYd1YJ5v8.jpg"
                ),

                "trailer_url": "",

                "duration": 163,

                "release_date": date(2023, 7, 12),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 9
            # =================================================

            {
                "slug": "the-hunger-games-catching-fire",

                "title": "The Hunger Games: Catching Fire",

                "description": (
                    "Katniss Everdeen and Peeta Mellark are forced back "
                    "into the arena as unrest spreads throughout Panem."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/vrQHDXjVmbYzadNWUFQF18Rz1qM.jpg"
                ),

                "trailer_url": "",

                "duration": 146,

                "release_date": date(2013, 11, 22),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # =================================================
            # MOVIE 10
            # =================================================

            {
                "slug": "a-quiet-place",

                "title": "A Quiet Place",

                "description": (
                    "A family struggles to survive in a world where "
                    "mysterious creatures hunt anything that makes a sound."
                ),

                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/nAU74GmpUk7t5iklEp3bufwDq4N.jpg"
                ),

                "trailer_url": "",

                "duration": 90,

                "release_date": date(2018, 4, 6),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },

        ]


        # =====================================================
        # CREATE MOVIES
        # =====================================================

        created_count = 0

        existing_count = 0


        for movie_data in movies:

            slug = movie_data["slug"]


            movie = Movie.objects.filter(
                slug=slug
            ).first()


            # ================================================
            # EXISTING MOVIE
            # ================================================

            if movie:

                existing_count += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"• Already exists: {movie.title}"
                    )
                )

                continue


            # ================================================
            # CREATE MOVIE
            # ================================================

            movie = Movie.objects.create(
                **movie_data
            )


            created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created: {movie.title}"
                )
            )


        # =====================================================
        # SUMMARY
        # =====================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Movie operation completed."
            )
        )

        self.stdout.write(
            f"Movies created: {created_count}"
        )

        self.stdout.write(
            f"Movies already existed: {existing_count}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "CineFlow movies are ready!"
            )
        )