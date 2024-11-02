from django.urls import re_path
from django.conf import settings

from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)


urlpatterns = [
    re_path(
        r"^login/$",
        LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    re_path(
        r"^logout/$",
        LogoutView.as_view(template_name="logout.html"),
        name="logout",
    ),
    re_path(
        r"^password_change/$",
        PasswordChangeView.as_view(template_name="password_change_form.html"),
        name="password_change",
    ),
    re_path(
        r"^password_change/done/$",
        PasswordChangeDoneView.as_view(
            template_name="password_change_done.html"
        ),
        name="password_change_done",
    ),
    re_path(
        r"^password_reset/$",
        PasswordResetView.as_view(
            template_name="password_reset_form.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            from_email=settings.VENUE["mailout_delivery_report_to"],
            extra_email_context=settings.VENUE,
        ),  # TODO make this work
        name="password_reset",
    ),
    re_path(
        r"^password_reset/done/$",
        PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    re_path(
        r"^reset/done/$",
        PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
