from datetime import timedelta
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from cinemas.models import Cinema, Screen, Seat
from movies.models import Movie
from showtimes.models import Showtime

from .models import Booking, BookingSeat, Payment
from .services import (
    create_assigned_hold,
    create_general_hold,
    confirm_booking,
    expire_booking,
    get_available_capacity,
    get_available_seat_count,
    get_available_seats,
    process_successful_payment,
)


class BookingServiceTestCase(TestCase):

    def setUp(self):
        # ---------------------------------------------------------
        # USER
        # ---------------------------------------------------------
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )

        # ---------------------------------------------------------
        # MOVIE
        # ---------------------------------------------------------
        self.movie = Movie.objects.create(
        title="Test Movie",
        slug="test-movie",
        description="A test movie.",
        duration=120,
        release_date=date.today(),
        age_rating="PG",
    )

        # ---------------------------------------------------------
        # CINEMA
        # ---------------------------------------------------------
        self.cinema = Cinema.objects.create(
            name="Test Cinema",
            slug="test-cinema",
            address="123 Cinema Street",
            city="Ibadan",
            state="Oyo",
            phone="08000000000",
            email="cinema@example.com",
        )

        # ---------------------------------------------------------
        # ASSIGNED SCREEN
        # ---------------------------------------------------------
        self.assigned_screen = Screen.objects.create(
            cinema=self.cinema,
            name="Screen 1",
            screen_type=Screen.ScreenType.STANDARD,
            capacity=10,
        )

        # Create assigned seats
        self.assigned_seats = []

        for row, number in [
            ("A", 1),
            ("A", 2),
            ("A", 3),
            ("A", 4),
            ("A", 5),
        ]:
            self.assigned_seats.append(
                Seat.objects.create(
                    screen=self.assigned_screen,
                    row=row,
                    number=number,
                )
            )

        # ---------------------------------------------------------
        # GENERAL ADMISSION SCREEN
        # ---------------------------------------------------------
        self.general_screen = Screen.objects.create(
            cinema=self.cinema,
            name="Screen 2",
            screen_type=Screen.ScreenType.STANDARD,
            capacity=10,
        )

        # ---------------------------------------------------------
        # ASSIGNED SHOWTIME
        # ---------------------------------------------------------
        self.assigned_showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.assigned_screen,
            show_date=timezone.localdate() + timedelta(days=1),
            start_time="18:00",
            ticket_price=Decimal("5000.00"),
            booking_mode=Showtime.BookingMode.ASSIGNED,
            status=Showtime.Status.SCHEDULED,
        )

        # ---------------------------------------------------------
        # GENERAL SHOWTIME
        # ---------------------------------------------------------
        self.general_showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.general_screen,
            show_date=timezone.localdate() + timedelta(days=1),
            start_time="20:00",
            ticket_price=Decimal("4000.00"),
            booking_mode=Showtime.BookingMode.GENERAL,
            status=Showtime.Status.SCHEDULED,
        )

    # =============================================================
    # ASSIGNED SEATING TESTS
    # =============================================================

    def test_get_available_seats_returns_all_seats_initially(self):
        available = get_available_seats(self.assigned_showtime)

        self.assertEqual(
            set(available),
            set(self.assigned_seats),
        )

    def test_create_assigned_hold(self):
        seat = self.assigned_seats[0]

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[seat],
        )

        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, Booking.Status.HELD)
        self.assertEqual(booking.ticket_quantity, 1)
        self.assertEqual(
            booking.total_amount,
            Decimal("5000.00"),
        )

        self.assertEqual(
            booking.booking_seats.count(),
            1,
        )

        self.assertEqual(
            booking.booking_seats.first().seat,
            seat,
        )

    def test_held_seat_is_not_available(self):
        seat = self.assigned_seats[0]

        create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[seat],
        )

        available = get_available_seats(
            self.assigned_showtime
        )

        self.assertNotIn(
            seat,
            available,
        )

        self.assertEqual(
            get_available_seat_count(self.assigned_showtime),
            4,
        )

    def test_cannot_hold_already_held_seat(self):
        seat = self.assigned_seats[0]

        create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[seat],
        )

        with self.assertRaises(ValidationError):
            create_assigned_hold(
                user=self.user,
                showtime=self.assigned_showtime,
                seat_ids=[seat],
            )

    def test_confirmed_booking_keeps_seats_unavailable(self):
        seats = self.assigned_seats[:2]

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=seats,
        )

        confirm_booking(booking)

        available = get_available_seats(
            self.assigned_showtime
        )

        for seat in seats:
            self.assertNotIn(
                seat,
                available,
            )

        self.assertEqual(
            get_available_seat_count(
                self.assigned_showtime
            ),
            3,
        )

    def test_expired_booking_releases_seats(self):
        seat = self.assigned_seats[0]

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[seat],
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        booking.save(
            update_fields=[
                "hold_expires_at",
                "updated_at",
            ]
        )

        expire_booking(booking)

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.EXPIRED,
        )

        self.assertFalse(
            BookingSeat.objects.filter(
                booking=booking,
            ).exists()
        )

        available = get_available_seats(
            self.assigned_showtime
        )

        self.assertIn(
            seat,
            available,
        )

    def test_expired_booking_cannot_be_confirmed(self):
        seat = self.assigned_seats[0]

        booking = create_assigned_hold(
            user=self.user,
            showtime=self.assigned_showtime,
            seat_ids=[seat],
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        booking.save(
            update_fields=[
                "hold_expires_at",
                "updated_at",
            ]
        )

        with self.assertRaises(ValidationError):
            confirm_booking(booking)

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.EXPIRED,
        )

    # =============================================================
    # GENERAL ADMISSION TESTS
    # =============================================================

    def test_general_admission_capacity(self):
        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            10,
        )

    def test_create_general_hold(self):
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
            Decimal("12000.00"),
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            7,
        )

    def test_general_hold_reduces_capacity(self):
        create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=4,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            6,
        )

    def test_general_hold_cannot_exceed_capacity(self):
        with self.assertRaises(ValidationError):
            create_general_hold(
                user=self.user,
                showtime=self.general_showtime,
                ticket_quantity=11,
            )

    def test_general_showtime_sold_out(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=10,
        )

        self.assertEqual(
            booking.ticket_quantity,
            10,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            0,
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
            ticket_quantity=4,
        )

        confirm_booking(booking)

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.CONFIRMED,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            6,
        )

    def test_expired_general_booking_releases_capacity(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=4,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            6,
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        booking.save(
            update_fields=[
                "hold_expires_at",
                "updated_at",
            ]
        )

        expire_booking(booking)

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.EXPIRED,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            10,
        )

    # =============================================================
    # CAPACITY / VALIDATION TESTS
    # =============================================================

    def test_general_capacity_reduces_correctly_with_multiple_bookings(self):
        create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=3,
        )

        second_user = User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="testpassword123",
        )

        create_general_hold(
            user=second_user,
            showtime=self.general_showtime,
            ticket_quantity=2,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            5,
        )

    def test_cancelled_showtime_cannot_be_booked(self):
        self.general_showtime.status = (
            Showtime.Status.CANCELLED
        )
        self.general_showtime.save(
            update_fields=["status", "updated_at"]
        )

        with self.assertRaises(ValidationError):
            create_general_hold(
                user=self.user,
                showtime=self.general_showtime,
                ticket_quantity=1,
            )

    def test_assigned_function_rejects_general_showtime(self):
        seat = self.assigned_seats[0]

        with self.assertRaises(ValidationError):
            create_assigned_hold(
                user=self.user,
                showtime=self.general_showtime,
                seat_ids=[seat],
            )

    def test_general_function_rejects_assigned_showtime(self):
        with self.assertRaises(ValidationError):
            create_general_hold(
                user=self.user,
                showtime=self.assigned_showtime,
                ticket_quantity=1,
            )

    # =============================================================
    # PAYMENT TESTS
    # =============================================================

    def test_payment_is_created_for_booking(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=2,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-TEST-001",
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        self.assertIsNotNone(payment)
        self.assertEqual(
            payment.booking,
            booking,
        )
        self.assertEqual(
            payment.amount,
            Decimal("8000.00"),
        )
        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_successful_payment_confirms_booking(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=2,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-SUCCESS-001",
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        process_successful_payment(payment)

        payment.refresh_from_db()
        booking.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.SUCCESSFUL,
        )

        self.assertEqual(
            booking.status,
            Booking.Status.CONFIRMED,
        )

        self.assertIsNone(
            booking.hold_expires_at,
        )

    def test_successful_payment_requires_pending_payment(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=1,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-SUCCESS-002",
            amount=booking.total_amount,
            status=Payment.Status.SUCCESSFUL,
            provider=Payment.Provider.TEST,
        )

        with self.assertRaises(ValidationError):
            process_successful_payment(payment)

    def test_successful_payment_requires_held_booking(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=1,
        )

        confirm_booking(booking)

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-SUCCESS-003",
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        with self.assertRaises(ValidationError):
            process_successful_payment(payment)

    def test_expired_booking_payment_fails(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=2,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-EXPIRED-001",
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        booking.save(
            update_fields=[
                "hold_expires_at",
                "updated_at",
            ]
        )

        with self.assertRaises(ValidationError):
            process_successful_payment(payment)

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.EXPIRED,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            10,
        )

    def test_payment_amount_mismatch_fails_payment(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=2,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-MISMATCH-001",
            amount=Decimal("1.00"),
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        with self.assertRaises(ValidationError):
            process_successful_payment(payment)

        payment.refresh_from_db()
        booking.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )

        self.assertEqual(
            booking.status,
            Booking.Status.HELD,
        )

    def test_successful_payment_reduces_general_capacity(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=3,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-CAPACITY-001",
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        process_successful_payment(payment)

        self.assertEqual(
            get_available_capacity(
                self.general_showtime
            ),
            7,
        )

    def test_expiring_booking_marks_pending_payment_failed(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=2,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-EXPIRATION-001",
            amount=booking.total_amount,
            status=Payment.Status.PENDING,
            provider=Payment.Provider.TEST,
        )

        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        booking.save(
            update_fields=[
                "hold_expires_at",
                "updated_at",
            ]
        )

        expire_booking(booking)

        payment.refresh_from_db()
        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking.Status.EXPIRED,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.FAILED,
        )

    def test_expiring_booking_does_not_change_successful_payment(self):
        booking = create_general_hold(
            user=self.user,
            showtime=self.general_showtime,
            ticket_quantity=1,
        )

        payment = Payment.objects.create(
            booking=booking,
            payment_reference="CFPAY-EXPIRATION-002",
            amount=booking.total_amount,
            status=Payment.Status.SUCCESSFUL,
            provider=Payment.Provider.TEST,
        )

        booking.status = Booking.Status.CONFIRMED
        booking.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )
        booking.save(
            update_fields=[
                "status",
                "hold_expires_at",
                "updated_at",
            ]
        )

        expire_booking(booking)

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.SUCCESSFUL,
        )