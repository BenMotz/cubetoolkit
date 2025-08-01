import datetime
import calendar

from django import forms
import django.db.models
from django.conf import settings
from crispy_forms.helper import FormHelper

# Custom form widgets:
from toolkit.diary.form_widgets import (
    HtmlTextarea,
    JQueryDateTimePicker,
    ChosenSelectMultiple,
)

import toolkit.diary.models
from collections import OrderedDict

from toolkit.diary.validators import validate_in_future


class RoleForm(forms.ModelForm):
    class Meta:
        model = toolkit.diary.models.Role
        fields = (
            "name",
            "standard",
        )


class DiaryIdeaForm(forms.ModelForm):
    class Meta:
        model = toolkit.diary.models.DiaryIdea
        fields = ("ideas",)


class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-sm-2"
        self.helper.field_class = "col-sm-10"

    class Meta:
        model = toolkit.diary.models.Event
        # Ensure soft wrapping is set for textareas:
        widgets = {
            # Use the custom WYSIWYG text editor widget:
            "copy": HtmlTextarea(attrs={"wrap": "soft"}),
            "copy_summary": forms.Textarea(attrs={"wrap": "soft"}),
            "terms": forms.Textarea(
                attrs={
                    "wrap": "soft",
                    "placeholder": f"e.g {settings.DEFAULT_TERMS_TEXT}",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "wrap": "soft",
                    "rows": 5,  # Arbitrary
                    "placeholder": "Programmer's notes - not visible to public",
                }
            ),
            "pricing": forms.TextInput(
                attrs={
                    "placeholder": (
                        "e.g. '\u00A30 Full / \u00A30 Concession' "
                        "or '\u00A30 advance, \u00A30 on the door'"
                    ),
                }
            ),
            "film_information": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Dir: [director], 1990, USA, 120 mins, "
                    "Cert: 15",
                }
            ),
            "pre_title": forms.TextInput(
                attrs={
                    "placeholder": (
                        (
                            f"Text displayed before / above the event"
                            f"name, e.g. '{settings.VENUE['name']} presents'"
                        )
                    ),
                }
            ),
            "post_title": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Text displayed after / below the event name,"
                        " e.g. 'with support from A Band'"
                    ),
                }
            ),
            "tags": ChosenSelectMultiple(width="70%"),
        }
        order = ("tags",)
        fields = (
            "name",
            "tags",
            "pricing",
            "ticket_link",
            "film_information",
            "pre_title",
            "post_title",
            "notes",
            "duration",
            "outside_hire",
            "private",
            "copy",
            "copy_summary",
            "terms",
        )

    def clean_copy_summary(self):
        copy_summary = self.cleaned_data.get("copy_summary", "")
        if len(copy_summary) > settings.PROGRAMME_COPY_SUMMARY_MAX_CHARS:
            raise forms.ValidationError(
                f"Copy summary must be {settings.PROGRAMME_COPY_SUMMARY_MAX_CHARS} "
                f"characters or fewer (currently {len(copy_summary)} characters)"
            )
        return copy_summary

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.all_showings_confirmed():
            terms = cleaned_data.get("terms", "")
            terms_word_count = len(terms.split())

            terms_not_required = cleaned_data.get(
                "tags"
            ).contains_tag_to_not_need_terms()

            if (
                terms_word_count < settings.PROGRAMME_EVENT_TERMS_MIN_WORDS
                and not terms_not_required
            ):
                msg = (
                    f"Event terms for confirmed event '{self.instance.name}' "
                    f"are missing or too short. Please enter at least "
                    f"{settings.PROGRAMME_EVENT_TERMS_MIN_WORDS} words."
                )
                self.add_error("terms", msg)
        return cleaned_data


class MediaItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-sm-2"
        self.helper.field_class = "col-sm-10"

    class Meta:
        model = toolkit.diary.models.MediaItem
        widgets = {
            "media_file": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/gif,image/png"}
            ),
        }
        exclude = ("mimetype", "caption")

    def clean_media_file(self):
        media_file = self.cleaned_data.get("media_file", None)
        if media_file:
            size_MB = media_file.size / 1048576.0
            max_MB = settings.PROGRAMME_MEDIA_MAX_SIZE_MB
            if size_MB > max_MB:
                raise forms.ValidationError(
                    f"Media file must be {max_MB} MB or less "
                    f"(uploaded file is {size_MB:.2f} MB)"
                )
        return media_file


class ShowingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.MULTIROOM_ENABLED:
            del self.fields["room"]
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-sm-2"
        self.helper.field_class = "col-sm-10"

    class Meta:
        model = toolkit.diary.models.Showing
        fields = (
            "room",
            "start",
            "booked_by",
            "confirmed",
            "hide_in_programme",
            "cancelled",
            "sold_out",
            "discounted",
        )

        widgets = {
            "start": JQueryDateTimePicker(),
        }

    def clean_confirmed(self):
        confirmed = self.cleaned_data["confirmed"]
        if (
            confirmed
            and self.instance.event_id
            and self.instance.event.terms_required()
            and not self.instance.event.terms_long_enough()
        ):

            raise forms.ValidationError(
                "Events require terms information "
                f'(unless they are tagged with one of {"/".join(sorted(settings.TAGS_WITHOUT_TERMS))}). '
                "Please add more details."
            )
        return confirmed

    def clean(self):
        if self.instance.original_start_in_past():
            self.cleaned_data["start"] = self.instance.start
            raise forms.ValidationError("Cannot amend a historic booking")
        return super().clean()


ShowingFormSet = forms.modelformset_factory(
    toolkit.diary.models.Showing,
    extra=1,
    form=ShowingForm,
)


class ShowingRotaNotesForm(forms.ModelForm):
    class Meta:
        model = toolkit.diary.models.Showing
        fields = ("rota_notes",)


def rota_form_factory(showing):
    # Dynamically generate a form to edit the rota for the given showing

    # Members for RotaForm class:
    members = OrderedDict()

    # All available roles:
    roles = toolkit.diary.models.Role.objects.order_by("name")

    # list of role IDs, to get stored in form and used to build rota from
    # submitted form data (as submitted data won't include IDs where rota
    # count is 0)
    _role_ids = []

    # Get all rota entries for showing, annotated with the maximum value of
    # "rank" for the role
    rota_entries = toolkit.diary.models.Role.objects.filter(
        rotaentry__showing_id=showing.pk
    ).annotate(max_rank=django.db.models.Max("rotaentry__rank"))

    # Build dict mapping role ID to max_rank
    rota_entry_count_by_role = dict(
        (role.pk, role.max_rank) for role in rota_entries
    )

    for role in roles:
        _role_ids.append(role.pk)
        if role.standard:
            # For each "standard" role, add an Integer field;
            members[f"role_{role.pk}"] = forms.IntegerField(
                min_value=0,
                max_value=settings.MAX_COUNT_PER_ROLE,
                required=True,
                label=role.name,
                initial=rota_entry_count_by_role.get(role.pk, 0),
                widget=forms.TextInput(attrs={"class": "rota_count"}),
            )

    # Add a MultipleChoiceField for all roles that aren't "standard"
    members["other_roles"] = forms.MultipleChoiceField(
        choices=((role.pk, role.name) for role in roles if not role.standard),
        # Don't have to have anything selected:
        required=False,
        # List of IDs which should be selected:
        initial=[entry.pk for entry in rota_entries if not entry.standard],
        # Fancy widget
        widget=ChosenSelectMultiple(width="100%"),
    )

    def get_rota(self):
        # Build a dict mapping role_id: number from submitted cleaned
        # data

        # Create empty results dict
        result = dict.fromkeys(self._role_ids, 0)
        for field, value in self.cleaned_data.items():
            if field == "other_roles":
                result.update(
                    (int(key, 10), 1)
                    for key in self.cleaned_data.get("other_roles", ())
                )
            if field.startswith("role_"):
                role_id = int(field.split("role_")[1], 10)
                result[role_id] = value
        return result

    members["_role_ids"] = _role_ids
    members["get_rota"] = get_rota

    return type("RotaForm", (forms.Form,), members)


class CloneShowingForm(forms.Form):
    # For cloning a showing, so only need very minimal extra details

    clone_start = forms.DateTimeField(
        required=True,
        validators=[validate_in_future],
        widget=JQueryDateTimePicker(),
    )
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)


class NewEventForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.MULTIROOM_ENABLED:
            del self.fields["room"]

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-sm-2"
        self.helper.field_class = "col-sm-10"

    room = forms.ModelChoiceField(
        queryset=toolkit.diary.models.Room.objects.all(), required=True
    )
    start = forms.DateTimeField(
        required=True,
        validators=[validate_in_future],
        widget=JQueryDateTimePicker(),
    )
    duration = forms.TimeField(required=True, initial=datetime.time(hour=1))
    number_of_bookings = forms.IntegerField(
        min_value=1,
        max_value=31,
        required=True,
        initial=1,
        help_text="Bookings will be created with the same start time on consecutive days",
    )
    event_name = forms.CharField(min_length=1, max_length=256, required=True)
    event_template = forms.ModelChoiceField(
        queryset=toolkit.diary.models.EventTemplate.objects.all(),
        required=True,
    )
    booked_by = forms.CharField(min_length=1, max_length=64, required=True)
    private = forms.BooleanField(required=False)
    outside_hire = forms.BooleanField(required=False)
    # confirmed = forms.BooleanField(required=False)
    discounted = forms.BooleanField(required=False)


class MailoutForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.html_mailout_enabled = kwargs.pop("html_mailout_enabled")
        super().__init__(*args, **kwargs)
        if not self.html_mailout_enabled:
            del self.fields["send_html"]
            del self.fields["body_html"]

    send_html = forms.BooleanField(
        label="Send HTML mailout", initial=True, required=False
    )

    subject = forms.CharField(max_length=128, required=True, label_suffix="")

    body_text = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"wrap": "soft", "cols": 80}),
    )

    body_html = forms.CharField(
        required=False,
        widget=HtmlTextarea(
            enable_tables=True, enable_iframes=False, height="120ex"
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        send_html = cleaned_data.get("send_html")
        body_html = cleaned_data.get("body_html")
        if send_html and not body_html:
            raise forms.ValidationError(
                "HTML body is empty. "
                "If you do not want to send an HTML email unset the 'Send HTML Mailout' option"
            )


class SearchForm(forms.Form):
    search_term = forms.CharField(
        label="Search for", required=False, widget=forms.widgets.SearchInput()
    )
    start_date = forms.DateTimeField(label="Search from", required=False)
    end_date = forms.DateTimeField(label="Search to", required=False)
    search_in_descriptions = forms.BooleanField(
        label="Also search event descriptions", required=False
    )

    def clean(self):
        cleaned_data = super().clean()

        # Check that either a search term or a search start or end date is
        # supplied:
        if len(cleaned_data.get("search_term", "").strip()) == 0 and not (
            cleaned_data.get("start_date") or cleaned_data.get("end_date")
        ):
            raise forms.ValidationError(
                "Must give either a search term or a " "date range"
            )

        return cleaned_data


class NewPrintedProgrammeForm(forms.ModelForm):
    # A custom form, so as to present a month/year choice for the date (if the
    # normal Date select is used there's no trivial way to hide the choice of
    # day of month - plus this allows the available range of years to be
    # limited to Cube founding through next year)

    year = forms.ChoiceField(
        choices=[
            (y, y)
            for y in range(
                settings.DAWN_OF_TIME, datetime.date.today().year + 2
            )
        ],
        initial=datetime.date.today().year,
    )
    # Use 'form_month' to avoid conflicting with 'month' field on the
    # underlying model -- see comment above.
    form_month = forms.ChoiceField(
        label="Month",
        choices=(list(zip(range(13), calendar.month_name))[1:]),
        initial=datetime.date.today().month,
    )

    class Meta:
        model = toolkit.diary.models.PrintedProgramme
        fields = ("form_month", "year", "programme", "designer", "notes")

    def clean(self):
        cleaned_data = super().clean()

        # Sets the "month" field on the model from the form data
        try:
            programme_month = datetime.date(
                int(cleaned_data["year"]), int(cleaned_data["form_month"]), 1
            )
        except (KeyError, ValueError, TypeError):
            raise forms.ValidationError(
                "Invalid/missing value for year " "and/or month"
            )

        self.instance.month = programme_month

        return cleaned_data
