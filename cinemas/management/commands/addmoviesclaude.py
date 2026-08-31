from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Movie


class Command(BaseCommand):

    help = "Add 20 more movies to CineFlow (does not touch existing seeded movies)."

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Adding CineFlow batch #2 movies..."
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
        # Poster URLs use TMDB's public image CDN (image.tmdb.org),
        # same as the original seed command.
        # Trailer URLs are verified official YouTube trailer links.
        #
        # If any single poster image doesn't load after you run this,
        # just grab the correct poster_path for that movie from its
        # page at themoviedb.org and swap it in below.
        #
        # =====================================================

        movies = [

            # =================================================
            # MOVIE 1
            # =================================================
            {
                "slug": "inception",
                "title": "Inception",
                "description": (
                    "A thief who steals corporate secrets through the use "
                    "of dream-sharing technology is given the inverse task "
                    "of planting an idea into the mind of a C.E.O."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/8IB2e4r4oVhHnANbnm7O3Tj6tF8.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=YoHD9XEInc0",
                "duration": 148,
                "release_date": date(2010, 7, 16),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 2
            # =================================================
            {
                "slug": "interstellar",
                "title": "Interstellar",
                "description": (
                    "A team of explorers travel through a wormhole in "
                    "space in an attempt to ensure humanity's survival."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=2LqzF5WauAw",
                "duration": 169,
                "release_date": date(2014, 11, 7),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 3
            # =================================================
            {
                "slug": "the-shawshank-redemption",
                "title": "The Shawshank Redemption",
                "description": (
                    "Two imprisoned men bond over a number of years, "
                    "finding solace and eventual redemption through acts "
                    "of common decency."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=P9mwtI82k6E",
                "duration": 142,
                "release_date": date(1994, 10, 14),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 4
            # =================================================
            {
                "slug": "pulp-fiction",
                "title": "Pulp Fiction",
                "description": (
                    "The lives of two mob hitmen, a boxer, a gangster's "
                    "wife, and a pair of diner bandits intertwine in four "
                    "tales of violence and redemption."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=tGpTpVyI_OQ",
                "duration": 154,
                "release_date": date(1994, 10, 14),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 5
            # =================================================
            {
                "slug": "the-godfather",
                "title": "The Godfather",
                "description": (
                    "The aging patriarch of an organized crime dynasty "
                    "transfers control of his clandestine empire to his "
                    "reluctant son."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=rqGJyUB1Q3s",
                "duration": 175,
                "release_date": date(1972, 3, 24),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 6
            # =================================================
            {
                "slug": "fight-club",
                "title": "Fight Club",
                "description": (
                    "An insomniac office worker looking for a way to "
                    "change his life crosses paths with a devil-may-care "
                    "soap maker, forming an underground fight club."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=BdJKm16Co6M",
                "duration": 139,
                "release_date": date(1999, 10, 15),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 7
            # =================================================
            {
                "slug": "forrest-gump",
                "title": "Forrest Gump",
                "description": (
                    "The presidencies of Kennedy and Johnson, Vietnam, "
                    "Watergate and other history unfold through the "
                    "perspective of an Alabama man with an IQ of 75."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=Mj9IA9tTfio",
                "duration": 142,
                "release_date": date(1994, 7, 6),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 8
            # =================================================
            {
                "slug": "titanic",
                "title": "Titanic",
                "description": (
                    "A seventeen-year-old aristocrat falls in love with a "
                    "kind but poor artist aboard the luxurious, ill-fated "
                    "R.M.S. Titanic."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=b0KYvGa_nN8",
                "duration": 195,
                "release_date": date(1997, 12, 19),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 9
            # =================================================
            {
                "slug": "jurassic-park",
                "title": "Jurassic Park",
                "description": (
                    "A pragmatic paleontologist visiting an almost "
                    "complete theme park is tasked with protecting a "
                    "couple of kids after a power failure causes the "
                    "park's cloned dinosaurs to run loose."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/b1xCNnyrPebIc7lg8FKkYQ4LrKw.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=_jKEqDKpJLw",
                "duration": 127,
                "release_date": date(1993, 6, 11),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 10
            # =================================================
            {
                "slug": "the-lion-king-1994",
                "title": "The Lion King",
                "description": (
                    "A young lion prince flees his kingdom after the "
                    "murder of his father, only to learn the true "
                    "meaning of responsibility and bravery years later."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=lFzVJEksoDY",
                "duration": 88,
                "release_date": date(1994, 6, 24),
                "age_rating": "G",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 11
            # =================================================
            {
                "slug": "spider-man-no-way-home",
                "title": "Spider-Man: No Way Home",
                "description": (
                    "With Spider-Man's identity now revealed, Peter asks "
                    "Doctor Strange for help, but a spell gone wrong "
                    "brings dangerous foes from other worlds."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=JfVOs4VSpmA",
                "duration": 148,
                "release_date": date(2021, 12, 17),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 12
            # =================================================
            {
                "slug": "top-gun-maverick",
                "title": "Top Gun: Maverick",
                "description": (
                    "After more than thirty years of service, Pete "
                    "'Maverick' Mitchell is called back to train a "
                    "detachment of graduates for a dangerous mission."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=qSqVVswa420",
                "duration": 130,
                "release_date": date(2022, 5, 27),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 13
            # =================================================
            {
                "slug": "oppenheimer",
                "title": "Oppenheimer",
                "description": (
                    "The story of J. Robert Oppenheimer's role in the "
                    "development of the atomic bomb during World War II."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=gHsqNYYdp0w",
                "duration": 180,
                "release_date": date(2023, 7, 21),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 14
            # =================================================
            {
                "slug": "barbie",
                "title": "Barbie",
                "description": (
                    "Barbie and Ken are having the time of their lives in "
                    "the seemingly perfect world of Barbie Land, until "
                    "they venture out into the real world."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=pBk4NYhWNMM",
                "duration": 114,
                "release_date": date(2023, 7, 21),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 15
            # =================================================
            {
                "slug": "dune",
                "title": "Dune",
                "description": (
                    "Paul Atreides, a brilliant young man, must travel to "
                    "the most dangerous planet in the universe to ensure "
                    "the future of his family and his people."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=8g18jFHCLXk",
                "duration": 155,
                "release_date": date(2021, 10, 22),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 16
            # =================================================
            {
                "slug": "dune-part-two",
                "title": "Dune: Part Two",
                "description": (
                    "Paul Atreides unites with Chani and the Fremen while "
                    "on a warpath of revenge against the conspirators who "
                    "destroyed his family."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=Way9Dexny3w",
                "duration": 166,
                "release_date": date(2024, 3, 1),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 17
            # =================================================
            {
                "slug": "joker",
                "title": "Joker",
                "description": (
                    "In 1981, a failed stand-up comedian turns to a life "
                    "of crime and chaos in Gotham City, slowly rising to "
                    "become the criminal mastermind known as the Joker."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=zAGVQLHvwOY",
                "duration": 122,
                "release_date": date(2019, 10, 4),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 18
            # =================================================
            {
                "slug": "the-wolf-of-wall-street",
                "title": "The Wolf of Wall Street",
                "description": (
                    "Based on the true story of Jordan Belfort, a young "
                    "stockbroker whose rise and fall centers on his "
                    "excess and corruption on Wall Street."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/34m2tygAYBGqA9MXKhRDtzYd4MR.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=iszwuX1AK6A",
                "duration": 180,
                "release_date": date(2013, 12, 25),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 19
            # =================================================
            {
                "slug": "parasite",
                "title": "Parasite",
                "description": (
                    "Greed and class discrimination threaten the newly "
                    "formed symbiotic relationship between the wealthy "
                    "Park family and the destitute Kim clan."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=isOGD_7hNIY",
                "duration": 132,
                "release_date": date(2019, 5, 30),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },

            # =================================================
            # MOVIE 20
            # =================================================
            {
                "slug": "whiplash",
                "title": "Whiplash",
                "description": (
                    "A promising young jazz drummer enrolls at a "
                    "cutthroat music conservatory where his dreams of "
                    "greatness are mentored by an instructor who will "
                    "stop at nothing to realize his student's potential."
                ),
                "poster_url": (
                    "https://image.tmdb.org/t/p/"
                    "w500/6uSPcdGNA2A6vJmCagXk0lHUZDD.jpg"
                ),
                "trailer_url": "https://www.youtube.com/watch?v=Df1xkYYbYrY",
                "duration": 106,
                "release_date": date(2014, 10, 10),
                "age_rating": "R",
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
                "CineFlow batch #2 movies are ready!"
            )
        )