from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.contrib.auth.models import User

from .models import Profile


class RegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
    )

    class Meta:

        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "An account with this email already exists. "
                "Please log in instead."
            )

        return email

class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter your username or email",
                "autocomplete": "username",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        ),
    )

    def clean(self):

        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and password:

            try:
                user = User.objects.get(
                    email__iexact=username_or_email
                )

                self.cleaned_data["username"] = user.username

            except User.DoesNotExist:
                pass

        return super().clean()


# ============================================================
# PROFILE FORM
# ============================================================

class ProfileForm(forms.ModelForm):

    class Meta:

        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
        ]

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "given-name",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "family-name",
                }
            ),

            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "readonly": "readonly",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "email",
                }
            ),
        }

        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "username": "Username",
            "email": "Email Address",
        }

    def clean_username(self):

        username = self.cleaned_data["username"]

        # Username is intentionally read-only.
        # We return the existing value rather than
        # allowing it to be changed.

        if self.instance.pk:
            return self.instance.username

        return username

    
    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        existing_user = User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).first()

        if existing_user:

            raise forms.ValidationError(
                "This email address is already associated "
                "with another account."
            )

        return email

class ProfileImageForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ["profile_image"]

        widgets = {
            "profile_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
        }

        labels = {
            "profile_image": "Profile Image",
        }