from django import forms
from django.core.validators import validate_email

from .models import MailoutJob

from ..diary.form_widgets import (
    JQueryDateTimePicker,
)


class JobForm(forms.ModelForm):
    class Meta:
        model = MailoutJob
        fields = (
            "send_at",
            "send_html",
            "subject",
            "body_text",
            "body_html",
        )
        widgets = {
            "send_at": JQueryDateTimePicker(),
            "send_html": forms.HiddenInput(),
            "subject": forms.HiddenInput(),
            "body_text": forms.HiddenInput(),
            "body_html": forms.HiddenInput(),
        }


class TestMailoutJobForm(forms.ModelForm):
    """Form for testing mailout job creation"""

    class Meta:
        model = MailoutJob
        fields = (
            "send_at",
            "subject",
            "body_text",
            "recipient_filter",
        )
        widgets = {
            "send_at": JQueryDateTimePicker(),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body_text": forms.Textarea(
                attrs={"class": "form-control", "rows": 10}
            ),
            "recipient_filter": forms.TextInput(
                attrs={"class": "form-control"}
            ),
        }
        labels = {
            "body_text": "Body",
            "recipient_filter": "Recipient",
        }

    def clean_recipient_filter(self):
        recipient_filter = self.cleaned_data.get("recipient_filter")
        if not recipient_filter or not recipient_filter.strip():
            raise forms.ValidationError(
                "A recipient email address is required"
            )

        # Validate that it's a valid email address
        email = recipient_filter.strip()
        try:
            validate_email(email)
        except forms.ValidationError:
            raise forms.ValidationError("Please enter a valid email address")

        return email
