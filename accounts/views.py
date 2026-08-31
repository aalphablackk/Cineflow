from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    LoginForm,
    ProfileForm,
    RegisterForm,
)


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.user.is_authenticated:

        return redirect(
            "movies:home"
        )

    if request.method == "POST":

        form = RegisterForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            login(
                request,
                user,
            )

            messages.success(
                request,
                "Your CineFlow account has been created successfully.",
            )

            return redirect(
                "movies:home"
            )

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:

        return redirect(
            "movies:home"
        )

    if request.method == "POST":

        form = LoginForm(
            request,
            data=request.POST,
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user,
            )

            messages.success(
                request,
                "Welcome back to CineFlow.",
            )

            return redirect(
                "movies:home"
            )

    else:

        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "You have been logged out successfully.",
        )

        return redirect(
            "movies:home"
        )

    return redirect(
        "movies:home"
    )


# ============================================================
# PASSWORD RESET
# ============================================================

class CineFlowPasswordResetView(
    PasswordResetView
):

    template_name = (
        "accounts/password_reset.html"
    )

    email_template_name = (
        "accounts/password_reset_email.txt"
    )

    subject_template_name = (
        "accounts/password_reset_subject.txt"
    )

    success_url = reverse_lazy(
        "accounts:password_reset_done"
    )


class CineFlowPasswordResetDoneView(
    PasswordResetDoneView
):

    template_name = (
        "accounts/password_reset_done.html"
    )


class CineFlowPasswordResetConfirmView(
    PasswordResetConfirmView
):

    template_name = (
        "accounts/password_reset_confirm.html"
    )

    success_url = reverse_lazy(
        "accounts:password_reset_complete"
    )

    def form_valid(self, form):

        print("================================")
        print("PASSWORD RESET FORM IS VALID")
        print("USER:", form.user)
        print("USERNAME:", form.user.username)
        print("================================")

        response = super().form_valid(form)

        print("PASSWORD RESET SAVED")

        return response

class CineFlowPasswordResetCompleteView(
    PasswordResetCompleteView
):

    template_name = (
        "accounts/password_reset_complete.html"
    )


# ============================================================
# PASSWORD CHANGE
# ============================================================

@login_required
def password_change(request):

    if request.method == "POST":

        form = PasswordChangeForm(
            request.user,
            request.POST,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your password has been changed successfully.",
            )

            return redirect(
                "accounts:password_change_done"
            )

    else:

        form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        "accounts/password_change.html",
        {
            "form": form,
        },
    )


@login_required
def password_change_done(request):

    return render(
        request,
        "accounts/password_change_done.html",
    )


# ============================================================
# PROFILE
# ============================================================

# ============================================================
# PROFILE
# ============================================================

@login_required
def profile(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your profile has been updated successfully.",
            )

            return redirect(
                "accounts:profile"
            )

    else:

        form = ProfileForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
            "form": form,
            "edit_profile_open": (
                request.method == "POST"
                and form.errors
            ),
        },
    )