from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        "register/",
        views.register,
        name="register",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),


    # ========================================================
    # PROFILE
    # ========================================================

    path(
        "profile/",
        views.profile,
        name="profile",
    ),


    # ========================================================
    # PASSWORD CHANGE
    # ========================================================

    path(
        "password-change/",
        views.password_change,
        name="password_change",
    ),

    path(
        "password-change/done/",
        views.password_change_done,
        name="password_change_done",
    ),


    # ========================================================
    # PASSWORD RESET
    # ========================================================

    path(
        "password-reset/",
        views.CineFlowPasswordResetView.as_view(),
        name="password_reset",
    ),

    path(
        "password-reset/done/",
        views.CineFlowPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),

    path(
        "password-reset/<uidb64>/<token>/",
        views.CineFlowPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),

    path(
        "password-reset/complete/",
        views.CineFlowPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),

]