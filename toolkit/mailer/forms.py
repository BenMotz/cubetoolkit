from django import forms

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
