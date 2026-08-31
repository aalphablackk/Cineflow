from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from cinemas.models import Cinema, Screen
from cinemas.services import generate_seats
from movies.models import Movie
from showtimes.models import Showtime

from .models import Booking, BookingSeat
from .services import (
    create_assigned_hold,
    create_general_hold,
    confirm_booking,
    expire_booking,
    get_available_capacity,
    get_available_seats,
)


class BookingServiceTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Create the common test data once for this test class.
        """

        # =====================================================
        # USER
        # =====================================================

        cls.user = User.objects.create_user(
            username="testcustomer",
            password="TestPassword123!",
        )

        # =====================================================
        # CINEMA
        # =====================================================

        cls.cinema = Cinema.objects.create(
            name="Test CineFlow Cinema",
            slug="test-cineflow-cinema",
            address="Test Address",
            city="Lagos",
            state="Lagos",
            is_active=True,
        )

        # =====================================================
        # ASSIGNED-SEATING SCREEN
        # =====================================================

        cls.assigned_screen = Screen.objects.create(
            cinema=cls.cinema,
            name="Assigned Screen",
            screen_type=Screen.ScreenType.STANDARD,
            capacity=12,
            is_active=True,
        )

        generate_seats(
            cls.assigned_screen,
            {
                "A": 4,
                "B": 4,
                "C": 4,
            },
        )

        # =====================================================
        # GENERAL-ADMISSION SCREEN
        # =====================================================

        cls.general_screen = Screen.objects.create(
            cinema=cls.cinema,
            name="General Screen",
            screen_type=Screen.ScreenType.VIP,
            capacity=15,
            is_active=True,
        )

        generate_seats(
            cls.general_screen,
            {
                "A": 5,
                "B": 5,
                "C": 5,
            },
        )

        # =====================================================
        # MOVIE
        # =====================================================

        cls.movie = Movie.objects.create(
            title="Test Movie",
            slug="test-movie",
            description="A movie used for automated tests.",
            duration=120,
            release_date=date.today(),
            age_rating="PG-13",
            status=Movie.Status.NOW_SHOWING,
        )

        # =====================================================
        # ASSIGNED SHOWTIME
        # =====================================================

        cls.assigned_showtime = Showtime.objects.create(
            movie=cls.movie,
            screen=cls.assigned_screen,
            show_date=date.today() + timedelta(days=1),
            start_time=time(14, 0),
            ticket_price=5000,
            booking_mode=Showtime.BookingMode.ASSIGNED,
            status=Showtime.Status.SCHEDULED,
        )

        # =====================================================
        # GENERAL SHOWTIME
        # =====================================================

        cls.general_showtime = Showtime.objects.create(
            movie=cls.movie,
            screen=cls.general_screen,
            show_date=date.today() + timedelta(days=1),
            start_time=time(18, 0),
            ticket_price=7000,
            booking_mode=Showtime.BookingMode.GENERAL,
            status=Showtime.Status.SCHEDULED,
        )

    # =========================================================
    # ASSIGNED SEATING
    # =========================================================

    def test_all_assigned_seats_are_available_initially(self):

        available_seats = get_available_seats(
            self.assigned_showtime
        )

        self.assertEqual(
            available_seats.count(),
            12,
        )

    def test_customer_can_hold_assigned_seats(self):

        seats = list(
            get_available_seats(
                self.assigned_showtime
            )[:2]
        )

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[
                seat.id
                for seat in seats
            ],
        )

        self.assertEqual(
            booking.status,
            Booking.Status.HELD,
        )

        self.assertEqual(
            booking.ticket_quantity,
            2,
        )

        self.assertEqual(
            booking.total_amount,
            10000,
        )

    def test_held_seats_are_not_available(self):

        seats = list(
            get_available_seats(
                self.assigned_showtime
            )[:2]
        )

        create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[
                seat.id
                for seat in seats
            ],
        )

        available_seats = get_available_seats(
            self.assigned_showtime
        )

        self.assertEqual(
            available_seats.count(),
            10,
        )

        available_ids = set(
            available_seats.values_list(
                "id",
                flat=True,
            )
        )

        self.assertNotIn(
            seats[0].id,
            available_ids,
        )

        self.assertNotIn(
            seats[1].id,
            available_ids,
        )

    def test_customer_cannot_hold_already_held_seat(self):

        seat = get_available_seats(
            self.assigned_showtime
        ).first()

        create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[seat.id],
        )

        with self.assertRaises(ValidationError):

            create_assigned_hold(
                user=self.user,
                showtime=self.assigned_showtime,
                seat_ids=[seat.id],
            )

    def test_confirmed_booking_keeps_seats_unavailable(self):

        seats = list(
            get_available_seats(
                self.assigned_showtime
            )[:2]
        )

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[
                seat.id
                for seat in seats
            ],
        )

        confirm_booking(booking)

        available_seats = get_available_seats(
            self.assigned_showtime
        )

        self.assertEqual(
            available_seats.count(),
            10,
        )

    def test_expired_booking_releases_seats(self):

        seats = list(
            get_available_seats(
                self.assigned_showtime
            )[:2]
        )

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[
                seat.id
                for seat in seats
            ],
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )

        booking.save(
            update_fields=[
                "hold_expires_at",
            ]
        )

        expire_booking(booking)

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.EXPIRED,
        )

        available_ids = set(
            get_available_seats(
                self.assigned_showtime
            ).values_list(
                "id",
                flat=True,
            )
        )

        self.assertIn(
            seats[0].id,
            available_ids,
        )

        self.assertIn(
            seats[1].id,
            available_ids,
        )

    def test_expired_booking_cannot_be_confirmed(self):

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[
                get_available_seats(
                    self.assigned_showtime
                ).first().id
            ],
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )

        booking.save(
            update_fields=[
                "hold_expires_at",
            ]
        )

        with self.assertRaises(ValidationError):

            confirm_booking(booking)

    # =========================================================
    # GENERAL ADMISSION
    # =========================================================

    def test_general_admission_starts_with_full_capacity(self):

        available_capacity = get_available_capacity(
            self.general_showtime
        )

        self.assertEqual(
            available_capacity,
            15,
        )

    def test_customer_can_hold_general_admission_tickets(self):

        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=3,
        )

        self.assertEqual(
            booking.status,
            Booking.Status.HELD,
        )

        self.assertEqual(
            booking.ticket_quantity,
            3,
        )

        self.assertEqual(
            booking.total_amount,
            21000,
        )

    def test_general_hold_reduces_available_capacity(self):

        create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=3,
        )

        available_capacity = get_available_capacity(
            self.general_showtime
        )

        self.assertEqual(
            available_capacity,
            12,
        )

    def test_general_admission_cannot_exceed_capacity(self):

        with self.assertRaises(ValidationError):

            create_general_hold(
                user=self.user,
                showtime=self.general_showtime,
                ticket_quantity=16,
            )

    def test_general_admission_sold_out(self):

        create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=15,
        )

        with self.assertRaises(ValidationError):

            create_general_hold(
                user=self.user,
                showtime=self.general_showtime,
                ticket_quantity=1,
            )

    def test_confirmed_general_booking_consumes_capacity(self):

        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=3,
        )

        confirm_booking(booking)

        available_capacity = get_available_capacity(
            self.general_showtime
        )

        self.assertEqual(
            available_capacity,
            12,
        )

    def test_expired_general_booking_releases_capacity(self):

        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=3,
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )

        booking.save(
            update_fields=[
                "hold_expires_at",
            ]
        )

        expire_booking(booking)

        available_capacity = get_available_capacity(
            self.general_showtime
        )

        self.assertEqual(
            available_capacity,
            15,
        )

    # =========================================================
    # SHOWTIME VALIDATION
    # =========================================================

    def test_cancelled_showtime_cannot_be_booked(self):

        self.assigned_showtime.status = (
            Showtime.Status.CANCELLED
        )

        self.assigned_showtime.save(
            update_fields=["status"]
        )

        seat = get_available_seats(
            self.assigned_showtime
        ).first()

        with self.assertRaises(ValidationError):

            create_assigned_hold(
                user=self.user,
                showtime=self.assigned_showtime,
                seat_ids=[seat.id],
            )

    def test_assigned_function_rejects_general_showtime(self):

        with self.assertRaises(ValidationError):

            create_assigned_hold(
                user=self.user,
                showtime=self.general_showtime,
                seat_ids=[1],
            )

    def test_general_function_rejects_assigned_showtime(self):

        with self.assertRaises(ValidationError):

            create_general_hold(
                user=self.user,
                showtime=self.assigned_showtime,
                ticket_quantity=1,
            )