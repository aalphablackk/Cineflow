from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


# ============================================================
# CUSTOM ADMIN USER CREATION FORM
# ============================================================

class AdminUserCreationForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        strip=False,
    )

    class Meta:
        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:

            self.add_error(
                "password2",
                "The two passwords do not match.",
            )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            user.save()

        return user


# ============================================================
# CUSTOM ADMIN USER CHANGE FORM
# ============================================================

class AdminUserChangeForm(forms.ModelForm):

    class Meta:
        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


# ============================================================
# USER ADMIN
# ============================================================

class CustomUserAdmin(UserAdmin):

    add_form = AdminUserCreationForm
    form = AdminUserChangeForm

    add_fieldsets = (
        (
            "Account Information",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                ),
            },
        ),

        (
            "Password",
            {
                "classes": ("wide",),
                "fields": (
                    "password1",
                    "password2",
                ),
            },
        ),

        (
            "Permissions",
            {
                "classes": ("wide",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "username",
                    "password",
                    "first_name",
                    "last_name",
                    "email",
                ),
            },
        ),

        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),

        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                ),
            },
        ),
    )


# ============================================================
# REGISTER CUSTOM USER ADMIN
# ============================================================

admin.site.unregister(User)

admin.site.register(
    User,
    CustomUserAdmin,
)