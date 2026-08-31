from django import forms

from .models import Showtime

from movies.models import Movie

from cinemas.models import (
    Cinema,
    Screen,
)


# ============================================================
# SHOWTIME FORM
# ============================================================

class ShowtimeForm(forms.ModelForm):

    cinema = forms.ModelChoiceField(
        queryset=Cinema.objects.none(),
        required=True,
        empty_label="Select cinema",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        label="Cinema",
    )


    class Meta:

        model = Showtime

        fields = [
            "movie",
            "cinema",
            "screen",
            "show_date",
            "start_time",
            "ticket_price",
            "booking_mode",
            "status",
        ]

        widgets = {

            "movie": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "screen": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "show_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "start_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "ticket_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Enter ticket price",
                }
            ),

            "booking_mode": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

        }

        labels = {

            "movie": "Movie",

            "screen": "Screen",

            "show_date": "Show Date",

            "start_time": "Start Time",

            "ticket_price": "Ticket Price",

            "booking_mode": "Booking Mode",

            "status": "Status",

        }


    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


        # ====================================================
        # CINEMAS
        # ====================================================

        self.fields["cinema"].queryset = (
            Cinema.objects
            .filter(
                is_active=True,
            )
            .order_by(
                "name",
            )
        )


        # ====================================================
        # MOVIES
        # ====================================================

        self.fields["movie"].queryset = (
            Movie.objects
            .order_by(
                "title",
            )
        )


        # ====================================================
        # DEFAULT SCREEN QUERYSET
        # ====================================================

        self.fields["screen"].queryset = (
            Screen.objects.none()
        )


        # ====================================================
        # POSTED CINEMA
        #
        # This is important when CREATE or EDIT changes cinema.
        # Django must allow screens belonging to the cinema
        # submitted in request.POST.
        # ====================================================

        if self.is_bound:

            cinema_id = self.data.get(
                "cinema"
            )

            if cinema_id:

                try:

                    cinema_id = int(
                        cinema_id
                    )

                    self.fields["screen"].queryset = (
                        Screen.objects
                        .filter(
                            cinema_id=cinema_id,
                            is_active=True,
                        )
                        .select_related(
                            "cinema",
                        )
                        .order_by(
                            "name",
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass


        # ====================================================
        # EDIT INSTANCE
        # ====================================================

        elif (
            self.instance
            and self.instance.pk
            and self.instance.screen_id
        ):

            current_screen = (
                self.instance.screen
            )

            current_cinema = (
                current_screen.cinema
            )


            # Initial cinema for edit modal

            self.fields["cinema"].initial = (
                current_cinema
            )


            # Normal active screens

            self.fields["screen"].queryset = (
                Screen.objects
                .filter(
                    cinema=current_cinema,
                    is_active=True,
                )
                .select_related(
                    "cinema",
                )
                .order_by(
                    "name",
                )
            )


            # Keep current inactive screen available
            # so an old showtime can still render correctly.

            if not current_screen.is_active:

                self.fields["screen"].queryset = (
                    Screen.objects
                    .filter(
                        cinema=current_cinema,
                    )
                    .select_related(
                        "cinema",
                    )
                    .order_by(
                        "name",
                    )
                )


    # ========================================================
    # CLEAN
    # ========================================================

    def clean(self):

        cleaned_data = (
            super().clean()
        )

        cinema = cleaned_data.get(
            "cinema"
        )

        screen = cleaned_data.get(
            "screen"
        )

        movie = cleaned_data.get(
            "movie"
        )

        ticket_price = cleaned_data.get(
            "ticket_price"
        )


        # ====================================================
        # SCREEN / CINEMA CONSISTENCY
        # ====================================================

        if cinema and screen:

            if (
                screen.cinema_id
                != cinema.id
            ):

                self.add_error(
                    "screen",
                    "The selected screen does not belong "
                    "to the selected cinema.",
                )


        # ====================================================
        # SCREEN ACTIVE CHECK
        # ====================================================

        if (
            screen
            and not screen.is_active
        ):

            self.add_error(
                "screen",
                "The selected screen is inactive.",
            )


        # ====================================================
        # CINEMA ACTIVE CHECK
        # ====================================================

        if (
            cinema
            and not cinema.is_active
        ):

            self.add_error(
                "cinema",
                "The selected cinema is inactive.",
            )


        # ====================================================
        # MOVIE REQUIRED
        # ====================================================

        if not movie:

            self.add_error(
                "movie",
                "Please select a movie.",
            )


        # ====================================================
        # PRICE
        # ====================================================

        if (
            ticket_price is not None
            and ticket_price < 0
        ):

            self.add_error(
                "ticket_price",
                "Ticket price cannot be negative.",
            )


        return cleaned_data