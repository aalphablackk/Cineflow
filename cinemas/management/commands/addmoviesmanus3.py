from datetime import date

from django.core.management.base import BaseCommand

from movies.models import Movie


class Command(BaseCommand):
    help = "Add additional movies to CineFlow without affecting existing movies."

    movies = [
        {
            "slug": "dune-part-two",
            "title": "Dune: Part Two",
            "description": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.",
            "poster_url": "https://img.youtube.com/vi/Way9Dexny3w/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=Way9Dexny3w",
            "duration": 166,
            "release_date": date(2024, 3, 1),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "oppenheimer",
            "title": "Oppenheimer",
            "description": "The story of J. Robert Oppenheimer and the race to develop the first atomic bomb.",
            "poster_url": "https://img.youtube.com/vi/uYPbbksJxIg/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=uYPbbksJxIg",
            "duration": 180,
            "release_date": date(2023, 7, 21),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "barbie",
            "title": "Barbie",
            "description": "Barbie leaves her perfect world for a thought-provoking journey into the real world with Ken.",
            "poster_url": "https://img.youtube.com/vi/pBk4NYhWNMM/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=pBk4NYhWNMM",
            "duration": 114,
            "release_date": date(2023, 7, 21),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "godzilla-x-kong-the-new-empire",
            "title": "Godzilla x Kong: The New Empire",
            "description": "Godzilla and Kong join forces against a colossal threat hidden within the Hollow Earth.",
            "poster_url": "https://img.youtube.com/vi/lV1OOlGwExM/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=lV1OOlGwExM",
            "duration": 115,
            "release_date": date(2024, 3, 29),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "inside-out-2",
            "title": "Inside Out 2",
            "description": "Riley enters her teenage years as new emotions disrupt the headquarters inside her mind.",
            "poster_url": "https://img.youtube.com/vi/LEjhY15eCx0/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=LEjhY15eCx0",
            "duration": 96,
            "release_date": date(2024, 6, 14),
            "age_rating": "PG",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "deadpool-and-wolverine",
            "title": "Deadpool & Wolverine",
            "description": "Deadpool's quiet life is upended when the Time Variance Authority recruits him for a dangerous mission with Wolverine.",
            "poster_url": "https://img.youtube.com/vi/73_1biulkYk/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=73_1biulkYk",
            "duration": 128,
            "release_date": date(2024, 7, 26),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "alien-romulus",
            "title": "Alien: Romulus",
            "description": "Young space colonists face a terrifying life-form while scavenging an abandoned space station.",
            "poster_url": "https://img.youtube.com/vi/OzY2r2JXsDM/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=OzY2r2JXsDM",
            "duration": 119,
            "release_date": date(2024, 8, 16),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "the-wild-robot",
            "title": "The Wild Robot",
            "description": "A shipwrecked service robot adapts to life on a remote island and becomes the guardian of an orphaned gosling.",
            "poster_url": "https://img.youtube.com/vi/67vbA5ZJdKQ/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=67vbA5ZJdKQ",
            "duration": 102,
            "release_date": date(2024, 9, 27),
            "age_rating": "PG",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "wicked",
            "title": "Wicked",
            "description": "A remarkable friendship between Elphaba and Glinda changes the fate of Oz.",
            "poster_url": "https://img.youtube.com/vi/6COmYeLsz4c/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=6COmYeLsz4c",
            "duration": 160,
            "release_date": date(2024, 11, 22),
            "age_rating": "PG",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "furiosa-a-mad-max-saga",
            "title": "Furiosa: A Mad Max Saga",
            "description": "Young Furiosa is torn from her homeland and must survive the brutal wasteland ruled by rival warlords.",
            "poster_url": "https://img.youtube.com/vi/XJMuhwVlca4/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=XJMuhwVlca4",
            "duration": 148,
            "release_date": date(2024, 5, 24),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "kingdom-of-the-planet-of-the-apes",
            "title": "Kingdom of the Planet of the Apes",
            "description": "Generations after Caesar, a young ape begins a journey that challenges a rising ape kingdom and humanity's survivors.",
            "poster_url": "https://img.youtube.com/vi/XtFI7SNtVpY/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=XtFI7SNtVpY",
            "duration": 145,
            "release_date": date(2024, 5, 10),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "civil-war",
            "title": "Civil War",
            "description": "Journalists race across a fractured United States while documenting a rapidly escalating civil conflict.",
            "poster_url": "https://img.youtube.com/vi/aDyQxtg0V2w/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=aDyQxtg0V2w",
            "duration": 109,
            "release_date": date(2024, 4, 12),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "challengers",
            "title": "Challengers",
            "description": "A former tennis prodigy coaches her champion husband through a losing streak while confronting their shared past.",
            "poster_url": "https://img.youtube.com/vi/MDnVk5jIJr0/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=MDnVk5jIJr0",
            "duration": 131,
            "release_date": date(2024, 4, 26),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "the-fall-guy",
            "title": "The Fall Guy",
            "description": "A battered stuntman returns to work and investigates the disappearance of the star of his ex-girlfriend's film.",
            "poster_url": "https://img.youtube.com/vi/j7jPnwVGdZ8/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=j7jPnwVGdZ8",
            "duration": 126,
            "release_date": date(2024, 5, 3),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "twisters",
            "title": "Twisters",
            "description": "A retired storm chaser is drawn back into the field and joins a reckless team studying a historic outbreak of tornadoes.",
            "poster_url": "https://img.youtube.com/vi/wdok0rZdmx4/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=wdok0rZdmx4",
            "duration": 122,
            "release_date": date(2024, 7, 19),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "a-quiet-place-day-one",
            "title": "A Quiet Place: Day One",
            "description": "A woman in New York fights to survive the first day of an invasion by creatures that hunt by sound.",
            "poster_url": "https://img.youtube.com/vi/YPY7J-flzE8/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=YPY7J-flzE8",
            "duration": 100,
            "release_date": date(2024, 6, 28),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "guardians-of-the-galaxy-vol-3",
            "title": "Guardians of the Galaxy Vol. 3",
            "description": "The Guardians embark on a dangerous mission to protect Rocket and defend the team's future.",
            "poster_url": "https://img.youtube.com/vi/JqcncLPi9zw/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=JqcncLPi9zw",
            "duration": 150,
            "release_date": date(2023, 5, 5),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "the-equalizer-3",
            "title": "The Equalizer 3",
            "description": "Robert McCall discovers that his new friends in southern Italy are under the control of dangerous criminals.",
            "poster_url": "https://img.youtube.com/vi/19ikl8vy4zs/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=19ikl8vy4zs",
            "duration": 109,
            "release_date": date(2023, 8, 30),
            "age_rating": "R",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "gran-turismo",
            "title": "Gran Turismo",
            "description": "A skilled gamer gets the chance to become a professional race-car driver through an unconventional competition.",
            "poster_url": "https://img.youtube.com/vi/GVPzGBvPrzw/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=GVPzGBvPrzw",
            "duration": 134,
            "release_date": date(2023, 8, 25),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
        {
            "slug": "the-creator",
            "title": "The Creator",
            "description": "An ex-special-forces agent is recruited to hunt down the creator of an advanced artificial intelligence.",
            "poster_url": "https://img.youtube.com/vi/ex3C1-5Dhb8/hqdefault.jpg",
            "trailer_url": "https://www.youtube.com/watch?v=ex3C1-5Dhb8",
            "duration": 133,
            "release_date": date(2023, 9, 29),
            "age_rating": "PG-13",
            "status": Movie.Status.NOW_SHOWING,
        },
    ]

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for movie_data in self.movies:

            slug = movie_data["slug"]

            if Movie.objects.filter(slug=slug).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped: {movie_data['title']} already exists."
                    )
                )
                skipped_count += 1
                continue

            movie = Movie.objects.create(**movie_data)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Added: {movie.title}"
                )
            )

            created_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Added {created_count} new movie(s). "
                f"Skipped {skipped_count} existing movie(s)."
            )
        )