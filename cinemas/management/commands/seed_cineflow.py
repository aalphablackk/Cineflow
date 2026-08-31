from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from cinemas.models import Cinema, Screen
from cinemas.services import generate_seats
from movies.models import Movie
from showtimes.models import Showtime


class Command(BaseCommand):

    help = "Create development data for CineFlow."

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "Creating CineFlow development data..."
            )
        )

        # =====================================================
        # CINEMA
        # =====================================================

        cinema, created = Cinema.objects.get_or_create(
            slug="cineflow-cinema",
            defaults={
                "name": "CineFlow Cinemas",
                "address": "Ikeja City Mall",
                "city": "Ikeja",
                "state": "Lagos",
                "phone": "+2348000000000",
                "email": "info@cineflow.test",
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Cinema created."
                )
            )
        else:
            self.stdout.write(
                "• Cinema already exists."
            )

        # =====================================================
        # SCREEN 1
        # =====================================================

        screen_1, created = Screen.objects.get_or_create(
            cinema=cinema,
            name="Screen 1",
            defaults={
                "screen_type": Screen.ScreenType.STANDARD,
                "capacity": 12,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Screen 1 created."
                )
            )

        # =====================================================
        # SCREEN 2
        # =====================================================

        screen_2, created = Screen.objects.get_or_create(
            cinema=cinema,
            name="Screen 2",
            defaults={
                "screen_type": Screen.ScreenType.VIP,
                "capacity": 15,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Screen 2 created."
                )
            )

        # =====================================================
        # SCREEN 3
        # =====================================================

        screen_3, created = Screen.objects.get_or_create(
            cinema=cinema,
            name="IMAX Screen",
            defaults={
                "screen_type": Screen.ScreenType.IMAX,
                "capacity": 20,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ IMAX Screen created."
                )
            )

        # =====================================================
        # GENERATE SCREEN 1 SEATS
        # =====================================================

        if not screen_1.seats.exists():

            generate_seats(
                screen_1,
                {
                    "A": 4,
                    "B": 4,
                    "C": 4,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Screen 1 seats created."
                )
            )

        # =====================================================
        # GENERATE SCREEN 2 SEATS
        # =====================================================

        if not screen_2.seats.exists():

            generate_seats(
                screen_2,
                {
                    "A": 5,
                    "B": 5,
                    "C": 5,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Screen 2 seats created."
                )
            )

        # =====================================================
        # GENERATE SCREEN 3 SEATS
        # =====================================================

        if not screen_3.seats.exists():

            generate_seats(
                screen_3,
                {
                    "A": 5,
                    "B": 5,
                    "C": 5,
                    "D": 5,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ IMAX seats created."
                )
            )

        # =====================================================
        # MOVIE 1
        # =====================================================

        movie_1, created = Movie.objects.update_or_create(
            slug="the-batman",
            defaults={
                "title": "The Batman",
                "description": (
                    "When a sadistic serial killer begins murdering "
                    "key political figures in Gotham, Batman is forced "
                    "to investigate the city's hidden corruption."
                ),
                "poster_url": (
                    "https://th.bing.com/th/id/OIP.SEI1wmiis6Jpcx1E7qTbaAHaEK?w=284&h=180&c=7&r=0&o=7&dpr=1.7&pid=1.7&rm=3"
                ),
                "trailer_url": "",
                "duration": 176,
                "release_date": date(2022, 3, 4),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        # =====================================================
        # MOVIE 2
        # =====================================================

        movie_2, created = Movie.objects.update_or_create(
            slug="dune-part-two",
            defaults={
                "title": "Dune: Part Two",
                "description": (
                    "Paul Atreides unites with Chani and the Fremen "
                    "while seeking revenge against the conspirators "
                    "who destroyed his family."
                ),
                "poster_url": (
                    "https://th.bing.com/th/id/OIP.b8HgqQtH3-pJh1fDR1jorAHaIo?w=132&h=180&c=7&r=0&o=7&dpr=1.7&pid=1.7&rm=3"
                ),
                "trailer_url": "",
                "duration": 166,
                "release_date": date(2024, 3, 1),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        # =====================================================
        # MOVIE 3
        # =====================================================

        movie_3, created = Movie.objects.update_or_create(
            slug="avatar-the-way-of-water",
            defaults={
                "title": "Avatar: The Way of Water",
                "description": (
                    "Jake Sully and Neytiri raise their family on "
                    "Pandora while facing a new threat that forces "
                    "them to seek refuge."
                ),
                "poster_url": (
                    "https://tse2.mm.bing.net/th/id/OIP.Lw6HNgAK4MfyTLHvzpIZ8QHaEK?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
                ),
                "trailer_url": "",
                "duration": 192,
                "release_date": date(2022, 12, 16),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )

        # =====================================================
        # MOVIE 4
        # =====================================================

        movie_4, created = Movie.objects.update_or_create(
            slug="oppenheimer",
            defaults={
                "title": "Oppenheimer",
                "description": (
                    "The story of J. Robert Oppenheimer and the "
                    "development of the first atomic bomb."
                ),
                "poster_url": (
                    "https://tse1.mm.bing.net/th/id/OIP.Oxz4RD27JiIxX-sP4Che0gHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
                ),
                "trailer_url": "",
                "duration": 180,
                "release_date": date(2023, 7, 21),
                "age_rating": "R",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        # =====================================================
        # MOVIE 5
        # =====================================================

        movie_5, created = Movie.objects.update_or_create(
            slug="interstellar",
            defaults={
                "title": "Interstellar",
                "description": (
                    "A team of explorers travels through a wormhole "
                    "in search of a new home for humanity."
                ),
                "poster_url": (
                    "https://tse2.mm.bing.net/th/id/OIP.uiaj_IMaC7h3NoieAhcmVwHaLG?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
                ),
                "trailer_url": "",
                "duration": 169,
                "release_date": date(2014, 11, 7),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        # =====================================================
        # MOVIE 6
        # =====================================================

        movie_6, created = Movie.objects.update_or_create(
            slug="inception",
            defaults={
                "title": "Inception",
                "description": (
                    "A skilled thief who enters people's dreams is "
                    "given a dangerous final mission."
                ),
                "poster_url": (
                    "https://tse2.mm.bing.net/th/id/OIP.b8WjJA8J2IJgblXaSliy3QHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
                ),
                "trailer_url": "",
                "duration": 148,
                "release_date": date(2010, 7, 16),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        # =====================================================
        # MOVIE 7
        # =====================================================

        movie_7, created = Movie.objects.update_or_create(
            slug="spider-man-no-way-home",
            defaults={
                "title": "Spider-Man: No Way Home",
                "description": (
                    "Spider-Man seeks help to restore his secret identity, "
                    "but the spell unleashes villains from other worlds."
                ),
                "poster_url": (
                    "https://tse3.mm.bing.net/th/id/OIP.2QkJYlB5TMLQO8SdegwnywHaLH?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
                ),
                "trailer_url": "",
                "duration": 148,
                "release_date": date(2021, 12, 17),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        # =====================================================
        # MOVIE 8
        # =====================================================

        movie_8, created = Movie.objects.update_or_create(
            slug="top-gun-maverick",
            defaults={
                "title": "Top Gun: Maverick",
                "description": (
                    "After more than thirty years of service, Maverick "
                    "returns to train a new generation of elite pilots."
                ),
                "poster_url": (
                    "https://th.bing.com/th/id/OIP.hwFbfFXvwWcXiVmVx3mmwAHaK-?r=0&o=7rm=3&rs=1&pid=ImgDetMain&o=7&rm=3"
                ),
                "trailer_url": "",
                "duration": 131,
                "release_date": date(2022, 5, 27),
                "age_rating": "PG-13",
                "status": Movie.Status.NOW_SHOWING,
            },
        )


        self.stdout.write(
            self.style.SUCCESS(
                "✓ Movies created/updated."
            )
        )

        # =====================================================
        # SHOW DATE
        # =====================================================

        show_date = date.today() + timedelta(days=1)

        # =====================================================
        # SHOWTIME 1
        # ASSIGNED SEATING
        # =====================================================

        Showtime.objects.get_or_create(
            movie=movie_1,
            screen=screen_1,
            show_date=show_date,
            start_time=time(14, 0),
            defaults={
                "ticket_price": 5000,
                "booking_mode": (
                    Showtime.BookingMode.ASSIGNED
                ),
                "status": Showtime.Status.SCHEDULED,
            },
        )

        # =====================================================
        # SHOWTIME 2
        # GENERAL ADMISSION
        # =====================================================

        Showtime.objects.get_or_create(
            movie=movie_1,
            screen=screen_2,
            show_date=show_date,
            start_time=time(18, 0),
            defaults={
                "ticket_price": 7000,
                "booking_mode": (
                    Showtime.BookingMode.GENERAL
                ),
                "status": Showtime.Status.SCHEDULED,
            },
        )

        # =====================================================
        # SHOWTIME 3
        # ASSIGNED SEATING
        # =====================================================

        Showtime.objects.get_or_create(
            movie=movie_2,
            screen=screen_1,
            show_date=show_date,
            start_time=time(19, 0),
            defaults={
                "ticket_price": 4500,
                "booking_mode": (
                    Showtime.BookingMode.ASSIGNED
                ),
                "status": Showtime.Status.SCHEDULED,
            },
        )

        # =====================================================
        # SHOWTIME 4
        # GENERAL ADMISSION
        # =====================================================

        Showtime.objects.get_or_create(
            movie=movie_3,
            screen=screen_3,
            show_date=show_date,
            start_time=time(21, 0),
            defaults={
                "ticket_price": 10000,
                "booking_mode": (
                    Showtime.BookingMode.GENERAL
                ),
                "status": Showtime.Status.SCHEDULED,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "✓ Showtimes created."
            )
        )

        # =====================================================
        # TEST CUSTOMER
        # =====================================================

        user, created = User.objects.get_or_create(
            username="testcustomer",
            defaults={
                "email": "testcustomer@cineflow.test",
                "first_name": "Test",
                "last_name": "Customer",
            },
        )

        if created:
            user.set_password(
                "TestPassword123!"
            )
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Test customer created."
                )
            )
        else:
            self.stdout.write(
                "• Test customer already exists."
            )

        # =====================================================
        # COMPLETE
        # =====================================================

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "CineFlow development data is ready!"
            )
        )

        self.stdout.write("")
        self.stdout.write(
            "Cinema: CineFlow Cinemas"
        )

        self.stdout.write(
            "Screens: 3"
        )

        self.stdout.write(
            "Screen 1 seats: 12"
        )

        self.stdout.write(
            "Screen 2 seats: 15"
        )

        self.stdout.write(
            "IMAX seats: 20"
        )

        self.stdout.write(
            "Movies: 3"
        )

        self.stdout.write(
            "Showtimes: 4"
        )

        self.stdout.write(
            "Test user: testcustomer"
        )

        