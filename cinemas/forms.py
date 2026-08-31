from django import forms

from .models import (
    Cinema,
    Screen,
    Seat,
)


# ============================================================
# CINEMA FORM
# ============================================================

class CinemaForm(forms.ModelForm):

    class Meta:

        model = Cinema

        fields = [
            "name",
            "slug",
            "address",
            "city",
            "state",
            "phone",
            "email",
            "is_active",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter cinema name",
                }
            ),

            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. cineflow-ikeja",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter full cinema address",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Ikeja",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Lagos",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 08012345678",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "cinema@example.com",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

        }

        labels = {

            "name": "Cinema Name",

            "slug": "URL Slug",

            "address": "Address",

            "city": "City",

            "state": "State",

            "phone": "Phone Number",

            "email": "Email Address",

            "is_active": "Active Cinema",

        }

# ============================================================
# SCREEN FORM
# ============================================================

class ScreenForm(forms.ModelForm):

    class Meta:

        model = Screen

        fields = [
            "name",
            "screen_type",
            "capacity",
            "is_active",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Screen 1",
                }
            ),

            "screen_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "capacity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Enter screen capacity",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

        }

        labels = {

            "name": "Screen Name",

            "screen_type": "Screen Type",

            "capacity": "Capacity",

            "is_active": "Active Screen",

        }
# ============================================================
# SEAT FORM
# ============================================================

class SeatForm(forms.ModelForm):

    class Meta:

        model = Seat

        fields = [
            "row",
            "number",
            "is_active",
        ]

        widgets = {

            "row": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. A",
                    "maxlength": 5,
                }
            ),

            "number": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "e.g. 1",
                }
            ),

            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

        }

        labels = {

            "row": "Seat Row",

            "number": "Seat Number",

            "is_active": "Active Seat",

        }

# ============================================================
# SEAT GENERATION FORM
# ============================================================

class SeatGenerationForm(forms.Form):

    start_row = forms.CharField(
        max_length=5,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. A",
                "maxlength": 5,
            }
        ),
        label="Starting Row",
    )

    end_row = forms.CharField(
        max_length=5,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. F",
                "maxlength": 5,
            }
        ),
        label="Ending Row",
    )

    seats_per_row = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "e.g. 20",
            }
        ),
        label="Seats Per Row",
    )