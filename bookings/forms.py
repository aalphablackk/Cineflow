from django import forms

from .models import Booking
from .services import get_available_seats


class GeneralBookingForm(forms.ModelForm):

    class Meta:

        model = Booking

        fields = [
            "ticket_quantity",
        ]

        widgets = {
            "ticket_quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
        }

        labels = {
            "ticket_quantity": "Number of Tickets",
        }

    def __init__(
        self,
        *args,
        available_capacity=None,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)

        if available_capacity is not None:

            self.fields[
                "ticket_quantity"
            ].widget.attrs[
                "max"
            ] = available_capacity

            self.fields[
                "ticket_quantity"
            ].help_text = (
                f"{available_capacity} tickets available."
            )


class AssignedBookingForm(forms.Form):

    seat_ids = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Your Seats",
    )

    def __init__(
        self,
        *args,
        showtime=None,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)

        if showtime:

            self.fields[
                "seat_ids"
            ].queryset = get_available_seats(
                showtime,
            )