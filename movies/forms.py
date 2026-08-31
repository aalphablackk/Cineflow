from django import forms

from .models import Movie


class StaffMovieForm(forms.ModelForm):

    class Meta:

        model = Movie

        fields = [
            "title",
            "slug",
            "description",
            "poster",
            "poster_url",
            "trailer_url",
            "duration",
            "release_date",
            "age_rating",
            "status",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Movie title",
                }
            ),

            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "movie-slug",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Movie description",
                }
            ),

            "poster": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "poster_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://...",
                }
            ),

            "trailer_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://youtube.com/...",
                }
            ),

            "duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Duration in minutes",
                    "min": 1,
                }
            ),

            "release_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "age_rating": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "PG-13",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }