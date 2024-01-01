from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import MySetPasswordForm


urlpatterns = [
    path("", views.index_page, name="index"),
    path("contact/", views.contact_page, name="contact"),
    path("terms-conditions/", views.terms_page, name="terms-conditions"),
    path("credentials/", views.credentials_page, name="credentials"),
    path("nav-payments/", views.nav_payments_page, name="nav-payments"),
    path("nav-planner/", views.nav_planner_page, name="nav-planner"),
    path("nav-medical/", views.nav_medical_page, name="nav-medical"),

    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("logout/", views.logout_user, name="logout"),

    path("user-profile/", views.user_profile, name="user-profile"),
    path("edit-account/", views.edit_account, name="edit-account"),
    path("delete-user/", views.delete_user, name="delete-user"),

    path("edit-access/", views.edit_access, name="edit-access"),
    path("delete-access/", views.delete_access, name="delete-access"),

    path(
        "reset_password/",
        auth_views.PasswordResetView.as_view(
            template_name="reset_password.html"),
        name="reset_password",
    ),
    path(
        "reset_password_sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="reset_password_sent.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="reset.html", form_class=MySetPasswordForm
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset_password_complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="reset_password_complete.html"
        ),
        name="password_reset_complete",
    ),
]
