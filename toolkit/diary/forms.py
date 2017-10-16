import datetime
import calendar

from django import forms
import django.db.models
from django.conf import settings
import six

# Custom form widgets:
from toolkit.diary.form_widgets import (HtmlTextarea, JQueryDateTimePicker,
                                        ChosenSelectMultiple)

import toolkit.diary.models
from collections import OrderedDict

from toolkit.diary.validators import validate_in_future


class RoleForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Role
        fields = ('name', 'standard',)


class DiaryIdeaForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.DiaryIdea
        fields = ('ideas',)


class EventForm(forms.ModelForm):

    class Meta(object):
        model = toolkit.diary.models.Event
        # Ensure soft wrapping is set for textareas:
        widgets = {
            # Use the custom WYSIWYG text editor widget:
            'copy': HtmlTextarea(attrs={'wrap': 'soft'}),
            'copy_summary': forms.Textarea(attrs={'wrap': 'soft'}),
            'terms': forms.Textarea(attrs={'wrap': 'soft'}),
            'notes': forms.Textarea(attrs={
                'wrap': 'soft',
                'rows': 5,  # Arbitrary
                'placeholder': "Programmer's notes - not visible to public",
                }),
            'pricing': forms.TextInput(attrs={
                'placeholder': (u"e.g. '\u00A30 Full / \u00A30 Concession' "
                                u"or '\u00A30 advance, \u00A30 on the door'"),
                }),
            'film_information': forms.TextInput(attrs={
                'placeholder': u"e.g. Dir: [director], 1990, USA, 120 mins, "
                               u"Cert: 15",
                }),
            'pre_title': forms.TextInput(attrs={
                'placeholder': (u"Text displayed before / above the event"
                                u"name, e.g. 'Cube Productions present'"),
                }),
            'post_title': forms.TextInput(attrs={
                'placeholder': (u"Text displayed after / below the event name,"
                                u" e.g. 'with support from A Band'"),
                }),
            'tags': ChosenSelectMultiple(width="70%"),
        }
        order = ('tags', )
        fields = ('name', 'tags', 'pricing', 'ticket_link', 'film_information',
                  'pre_title',
                  'post_title', 'notes', 'duration', 'outside_hire', 'private',
                  'copy', 'copy_summary', 'terms')

    def clean_copy_summary(self):
        copy_summary = self.cleaned_data.get(u'copy_summary', u'')
        if len(copy_summary) > settings.PROGRAMME_COPY_SUMMARY_MAX_CHARS:
            raise forms.ValidationError(
                u"Copy summary must be {0} characters or fewer (currently {1} "
                u"characters)".format(
                    settings.PROGRAMME_COPY_SUMMARY_MAX_CHARS,
                    len(copy_summary)
                ))
        return copy_summary


class MediaItemForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.MediaItem
        widgets = {
            'media_file': forms.ClearableFileInput(attrs={
                    'accept': 'image/jpeg,image/gif,image/png'}),
        }
        exclude = ('mimetype', 'caption')

    def clean_media_file(self):
        media_file = self.cleaned_data.get(u'media_file', None)
        if media_file:
            size_MB = media_file.size / 1048576.0
            max_MB = settings.PROGRAMME_MEDIA_MAX_SIZE_MB
            if size_MB > max_MB:
                raise forms.ValidationError(
                    u"Media file must be {0} MB or less "
                    u"(uploaded file is {1:.2f} MB)"
                    .format(max_MB, size_MB))
        return media_file


class ShowingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ShowingForm, self).__init__(*args, **kwargs)
        if not settings.MULTIROOM_ENABLED:
            del self.fields['room']

    class Meta(object):
        model = toolkit.diary.models.Showing
        fields = ('room', 'start', 'booked_by', 'confirmed',
                  'hide_in_programme', 'cancelled', 'sold_out',
                  'discounted', )

        widgets = {
            'start': JQueryDateTimePicker(),
        }


class ShowingRotaNotesForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Showing
        fields = ('rota_notes',)


def rota_form_factory(showing):
    # Dynamically generate a form to edit the rota for the given showing

    # Members for RotaForm class:
    members = OrderedDict()

    # All available roles:
    roles = toolkit.diary.models.Role.objects.order_by('name')

    # list of role IDs, to get stored in form and used to build rota from
    # submitted form data (as submitted data won't include IDs where rota
    # count is 0)
    _role_ids = []

    # Get all rota entries for showing, annotated with the maximum value of
    # "rank" for the role
    rota_entries = (
        toolkit.diary.models.Role
                            .objects.filter(rotaentry__showing_id=showing.pk)
                                    .annotate(max_rank=django.db.models.Max(
                                        'rotaentry__rank')))

    # Build dict mapping role ID to max_rank
    rota_entry_count_by_role = dict(
        (role.pk, role.max_rank) for role in rota_entries)

    for role in roles:
        _role_ids.append(role.pk)
        if role.standard:
            # For each "standard" role, add an Integer field;
            members[u"role_{0}".format(role.pk)] = (
                forms.IntegerField(
                    min_value=0, max_value=settings.MAX_COUNT_PER_ROLE,
                    required=True, label=role.name,
                    initial=rota_entry_count_by_role.get(role.pk, 0),
                    widget=forms.TextInput(attrs={'class': 'rota_count'}))
            )

    # Add a MultipleChoiceField for all roles that aren't "standard"
    members['other_roles'] = forms.MultipleChoiceField(
        ((role.pk, role.name) for role in roles if not role.standard),
        # Don't have to have anything selected:
        required=False,
        # List of IDs which should be selected:
        initial=(entry.pk for entry in rota_entries),
        help_text='Hold down "Control", or "Command" on a Mac, to select more '
                  'than one.'
    )

    def get_rota(self):
        # Build a dict mapping role_id: number from submitted cleaned
        # data

        # Create empty results dict
        result = dict.fromkeys(self._role_ids, 0)
        for field, value in six.iteritems(self.cleaned_data):
            if field == 'other_roles':
                result.update(
                    (int(key, 10), 1) for key in
                    self.cleaned_data.get('other_roles', ())
                )
            if field.startswith('role_'):
                role_id = int(field.split('role_')[1], 10)
                result[role_id] = value
        return result

    members['_role_ids'] = _role_ids
    members['get_rota'] = get_rota

    return type("RotaForm", (forms.Form,), members)


class CloneShowingForm(forms.Form):
    # For cloning a showing, so only need very minimal extra details

    clone_start = forms.DateTimeField(required=True,
                                      validators=[validate_in_future],
                                      widget=JQueryDateTimePicker())
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)


class NewEventForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(NewEventForm, self).__init__(*args, **kwargs)
        if not settings.MULTIROOM_ENABLED:
            del self.fields['room']

    room = forms.ModelChoiceField(
        queryset=toolkit.diary.models.Room.objects.all(),
        required=True)
    start = forms.DateTimeField(
        required=True,
        validators=[validate_in_future],
        widget=JQueryDateTimePicker())
    duration = forms.TimeField(
        required=True,
        initial=datetime.time(hour=1))
    number_of_days = forms.IntegerField(
        min_value=1, max_value=31, required=True, initial=1)
    event_name = forms.CharField(
        min_length=1, max_length=256, required=True)
    event_template = forms.ModelChoiceField(
        queryset=toolkit.diary.models.EventTemplate.objects.all(),
        required=True)
    booked_by = forms.CharField(min_length=1, max_length=64, required=True)
    private = forms.BooleanField(required=False)
    outside_hire = forms.BooleanField(required=False)
    confirmed = forms.BooleanField(required=False)
    discounted = forms.BooleanField(required=False)


class MailoutForm(forms.Form):
    subject = forms.CharField(max_length=128, required=True, label_suffix='')
    body = forms.CharField(
            required=True,
            widget=forms.Textarea(attrs={'wrap': 'soft', 'cols': 80}))


class MailoutTestForm(forms.Form):
    address = forms.EmailField(required=True)
    subject = forms.CharField(max_length=128, required=True)
    body = forms.CharField(
            required=True,
            widget=forms.Textarea(attrs={'wrap': 'soft', 'cols': 80}))


class SearchForm(forms.Form):
    search_term = forms.CharField(label="Search for", required=False)
    start_date = forms.DateTimeField(label="Search from", required=False)
    end_date = forms.DateTimeField(label="Search to", required=False)
    search_in_descriptions = forms.BooleanField(
        label="Also search event descriptions", required=False)

    def clean(self):
        cleaned_data = super(SearchForm, self).clean()

        # Check that either a search term or a search start or end date is
        # supplied:
        if (len(cleaned_data.get('search_term', '').strip()) == 0 and not
                (cleaned_data.get('start_date') or
                 cleaned_data.get('end_date'))):
            raise forms.ValidationError("Must give either a search term or a "
                                        "date range")

        return cleaned_data


class NewPrintedProgrammeForm(forms.ModelForm):
    # A custom form, so as to present a month/year choice for the date (if the
    # normal Date select is used there's no trivial way to hide the choice of
    # day of month - plus this allows the available range of years to be
    # limited to Cube founding through next year)

    year = forms.ChoiceField(
        choices=[
            (y, y) for y in six.moves.range(settings.DAWN_OF_TIME,
                                            datetime.date.today().year + 2)
        ],
        initial=datetime.date.today().year
    )
    month = forms.ChoiceField(
        choices=(list(zip(range(13), calendar.month_name))[1:]),
        initial=datetime.date.today().month
    )

    class Meta(object):
        model = toolkit.diary.models.PrintedProgramme
        fields = ('month', 'programme', 'designer', 'notes')

    def clean(self):
        cleaned_data = super(NewPrintedProgrammeForm, self).clean()

        # Sets the "month" field on the model from the form data
        try:
            programme_month = datetime.date(
                int(cleaned_data['year']),
                int(cleaned_data['month']),
                1
            )
        except (KeyError, ValueError, TypeError):
            raise forms.ValidationError("Invalid/missing value for year "
                                        "and/or month")

        self.instance.month = programme_month

        return cleaned_data


class TagForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.EventTag
        fields = ('name',)
