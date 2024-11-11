from django import forms

from toolkit.diary.form_widgets import HtmlTextarea

from .models import MailoutJob


class JobForm(forms.ModelForm):
    class Meta:
        model = MailoutJob
        fields = (
            "send_at",
            "send_html",
            "subject",
            "body_text",
            "body_html",
            "recipient_filter",
        )
        widgets = {
            "subject": forms.TextInput(),
            "body_text": forms.Textarea(attrs={"wrap": "soft", "cols": 80}),
            "body_html": HtmlTextarea(
                enable_tables=True, enable_iframes=False, height="120ex"
            ),
        }
