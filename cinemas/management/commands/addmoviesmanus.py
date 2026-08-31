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

                "trailer_url": "https://www.youtube.com/watch?v=TcMBFSGVi1c",

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

                "trailer_url": "https://www.youtube.com/watch?v=qEVUtrk8_B4",

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

                "trailer_url": "https://www.youtube.com/watch?v=_Z3QKkl1WyM",

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

                "trailer_url": "https://www.youtube.com/watch?v=u3V5KDHRQvk",

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

                "trailer_url": "https://www.youtube.com/watch?v=vKQi3bBA1y8",

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

                "trailer_url": "https://www.youtube.com/watch?v=owK1qxDselE",

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

                "trailer_url": "https://www.youtube.com/watch?v=EXeTwQWrcwY",

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

                "trailer_url": "https://www.youtube.com/watch?v=avz06PDqDbM",

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

                "trailer_url": "https://www.youtube.com/watch?v=EAzGXqJSDJ8",

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

                "trailer_url": "https://www.youtube.com/watch?v=WR7cc5t7tv8",

                "duration": 90,

                "release_date": date(2018, 4, 6),

                "age_rating": "PG-13",

                "status": Movie.Status.NOW_SHOWING,
            },


            # MOVIE 11
            {
                "slug": "inception",
                "title": "Inception",
                "description": "A skilled thief who steals secrets through shared dreams is offered a chance to erase his past by planting an idea in a target's mind.",
                "poster_url": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=YoHD9XEInc0",
                "duration": 148,
                "release_date": date(2010, 7, 16),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 12
            {
                "slug": "interstellar",
                "title": "Interstellar",
                "description": "Explorers travel through a wormhole in space in search of a new home for humanity as Earth approaches an environmental collapse.",
                "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=zSWdZVtXT7E",
                "duration": 169,
                "release_date": date(2014, 11, 7),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 13
            {
                "slug": "oppenheimer",
                "title": "Oppenheimer",
                "description": "Physicist J. Robert Oppenheimer leads the scientific effort that creates the first atomic bomb during World War II.",
                "poster_url": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=uYPbbksJxIg",
                "duration": 180,
                "release_date": date(2023, 7, 21),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 14
            {
                "slug": "dune",
                "title": "Dune",
                "description": "A gifted young nobleman must travel to the most dangerous planet in the universe to protect his family and people.",
                "poster_url": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=n9xhJrPXop4",
                "duration": 155,
                "release_date": date(2021, 10, 22),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 15
            {
                "slug": "dune-part-two",
                "title": "Dune: Part Two",
                "description": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.",
                "poster_url": "https://image.tmdb.org/t/p/w500/6izwz7rsy95ARzTR3poZ8H6c5pp.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=Way9Dexny3w",
                "duration": 166,
                "release_date": date(2024, 3, 1),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 16
            {
                "slug": "spider-man-no-way-home",
                "title": "Spider-Man: No Way Home",
                "description": "Peter Parker asks Doctor Strange to restore his secret identity, but the spell opens the door to villains from other worlds.",
                "poster_url": "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=JfVOs4VSpmA",
                "duration": 148,
                "release_date": date(2021, 12, 17),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 17
            {
                "slug": "avatar-the-way-of-water",
                "title": "Avatar: The Way of Water",
                "description": "Jake Sully and Neytiri build a family and seek refuge with an ocean-dwelling Na'vi clan when an old threat returns.",
                "poster_url": "https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=d9MyW72ELq0",
                "duration": 192,
                "release_date": date(2022, 12, 16),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 18
            {
                "slug": "top-gun-maverick",
                "title": "Top Gun: Maverick",
                "description": "After decades as one of the Navy's top aviators, Pete Mitchell trains a new generation for a dangerous mission.",
                "poster_url": "https://image.tmdb.org/t/p/w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=qSqVVswa420",
                "duration": 130,
                "release_date": date(2022, 5, 27),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 19
            {
                "slug": "barbie",
                "title": "Barbie",
                "description": "Barbie leaves her perfect world for a journey of self-discovery in the real world alongside Ken.",
                "poster_url": "https://image.tmdb.org/t/p/w500/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=pBk4NYhWNMM",
                "duration": 114,
                "release_date": date(2023, 7, 21),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 20
            {
                "slug": "the-batman",
                "title": "The Batman",
                "description": "Batman investigates a series of cryptic crimes that expose corruption at the heart of Gotham City.",
                "poster_url": "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=mqqft2x_Aa4",
                "duration": 176,
                "release_date": date(2022, 3, 4),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 21
            {
                "slug": "everything-everywhere-all-at-once",
                "title": "Everything Everywhere All at Once",
                "description": "An overwhelmed laundromat owner discovers that parallel-universe versions of herself need her help to save existence.",
                "poster_url": "https://image.tmdb.org/t/p/w500/w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=wxN1T1uxQ2g",
                "duration": 140,
                "release_date": date(2022, 4, 8),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 22
            {
                "slug": "parasite",
                "title": "Parasite",
                "description": "A struggling family gradually enters the lives of a wealthy household, with consequences that change both families forever.",
                "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=5xH0HfJHsaY",
                "duration": 132,
                "release_date": date(2019, 11, 8),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 23
            {
                "slug": "the-shawshank-redemption",
                "title": "The Shawshank Redemption",
                "description": "A banker sentenced to life in prison forms an enduring friendship and quietly holds on to hope.",
                "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=6hB3S9bIaco",
                "duration": 142,
                "release_date": date(1994, 9, 23),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 24
            {
                "slug": "pulp-fiction",
                "title": "Pulp Fiction",
                "description": "Interwoven stories of criminals, a boxer, and unexpected survivors unfold across Los Angeles.",
                "poster_url": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=s7EdQ4FqbhY",
                "duration": 154,
                "release_date": date(1994, 10, 14),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },
            # MOVIE 25
            {
                "slug": "the-lord-of-the-rings-the-fellowship-of-the-ring",
                "title": "The Lord of the Rings: The Fellowship of the Ring",
                "description": "A young hobbit begins a perilous journey to destroy a powerful ring before its creator can reclaim it.",
                "poster_url": "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=V75dMMIW2B4",
                "duration": 178,
                "release_date": date(2001, 12, 19),
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