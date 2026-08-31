from django.db import transaction

from .models import Screen, Seat


MAX_ROWS = 26
MAX_SEATS_PER_ROW = 50
MAX_SEATS_PER_SCREEN = 500


@transaction.atomic
def generate_seats(screen, layout):
    """
    Generate seats for a screen.

    Example:

        {
            "A": 4,
            "B": 5,
            "C": 3,
        }

    Generates:

        A1 A2 A3 A4
        B1 B2 B3 B4 B5
        C1 C2 C3
    """

    # ---------------------------------------------------------
    # Validate screen
    # ---------------------------------------------------------

    if not isinstance(screen, Screen):
        raise ValueError(
            "We couldn't create the seat layout because "
            "the selected screen is invalid."
        )

    # ---------------------------------------------------------
    # Validate layout
    # ---------------------------------------------------------

    if not isinstance(layout, dict) or not layout:
        raise ValueError(
            "Please provide a seat layout before generating seats."
        )

    # ---------------------------------------------------------
    # Validate number of rows
    # ---------------------------------------------------------

    if len(layout) > MAX_ROWS:
        raise ValueError(
            f"This screen can have a maximum of "
            f"{MAX_ROWS} rows."
        )

    total_seats = 0

    # ---------------------------------------------------------
    # Validate each row
    # ---------------------------------------------------------

    for row, seat_count in layout.items():

        if not isinstance(row, str) or not row.strip():
            raise ValueError(
                "Each row must have a valid row name."
            )

        if not isinstance(seat_count, int) or seat_count <= 0:
            raise ValueError(
                f"Row {row} must contain at least one seat."
            )

        if seat_count > MAX_SEATS_PER_ROW:
            raise ValueError(
                f"Row {row} can have a maximum of "
                f"{MAX_SEATS_PER_ROW} seats."
            )

        total_seats += seat_count

    # ---------------------------------------------------------
    # Validate total screen capacity
    # ---------------------------------------------------------

    if total_seats > MAX_SEATS_PER_SCREEN:
        raise ValueError(
            f"This seat layout contains {total_seats} seats, "
            f"which exceeds the maximum allowed capacity of "
            f"{MAX_SEATS_PER_SCREEN} seats."
        )

    # ---------------------------------------------------------
    # Ensure layout matches screen capacity
    # ---------------------------------------------------------

    if total_seats != screen.capacity:
        raise ValueError(
            f"The seat layout contains {total_seats} seats, "
            f"but {screen.name} has a capacity of "
            f"{screen.capacity}. "
            f"Please adjust the number of seats and try again."
        )

    # ---------------------------------------------------------
    # Prevent duplicate generation
    # ---------------------------------------------------------

    if screen.seats.exists():
        raise ValueError(
            f"Seats have already been created for {screen.name}. "
            f"Please edit the existing layout instead of "
            f"generating another one."
        )

    # ---------------------------------------------------------
    # Create seats
    # ---------------------------------------------------------

    seats = []

    for row, seat_count in layout.items():

        row = row.strip().upper()

        for number in range(1, seat_count + 1):

            seats.append(
                Seat(
                    screen=screen,
                    row=row,
                    number=number,
                )
            )

    Seat.objects.bulk_create(seats)

    return seats