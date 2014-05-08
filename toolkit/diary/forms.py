import datetime
import calendar

from django import forms
import django.db.models
from django.conf import settings

# Custom form widgets:
from toolkit.diary.form_widgets import (HtmlTextarea, JQueryDateTimePicker,
                                        ChosenSelectMultiple)

import toolkit.diary.models
from toolkit.util.ordereddict import OrderedDict

from toolkit.diary.validators import validate_in_future


class RoleForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Role
        fields = ('name', 'standard')


class DiaryIdeaForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.DiaryIdea


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
            'tags': ChosenSelectMultiple(width="70%"),
        }
        order = ('tags', )
        fields = ('name', 'tags', 'notes', 'duration', 'outside_hire',
                  'private', 'copy', 'copy_summary', 'terms')


class MediaItemForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.MediaItem
        widgets = {
            'media_file': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/gif,image/png'}),
        }
        exclude = ('mimetype', 'caption')


class ShowingForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Showing
        # Exclude these for now:
        exclude = ('event', 'extra_copy', 'extra_copy_summary', 'roles')

        widgets = {
            'start': JQueryDateTimePicker(),
        }


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

    # Get all rota entries for showing, annotated with the maximum value of "rank" for the role
    rota_entries = (toolkit.diary.models.Role
                                        .objects.filter(rotaentry__showing_id=showing.pk)
                                                .annotate(max_rank=django.db.models.Max('rotaentry__rank')))

    # Build dict mapping role ID to max_rank
    rota_entry_count_by_role = dict((role.pk, role.max_rank) for role in rota_entries)

    for role in roles:
        _role_ids.append(role.pk)
        if role.standard:
            # For each "standard" role, add an Integer field;
            members[u"role_{0}".format(role.pk)] = (
                forms.IntegerField(min_value=0, max_value=settings.MAX_COUNT_PER_ROLE, required=True, label=role.name,
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
        help_text='Hold down "Control", or "Command" on a Mac, to select more than one.'
    )

    def get_rota(self):
        # Build a dict mapping role_id: number from submitted cleaned
        # data

        # Create empty results dict
        result = dict.fromkeys(self._role_ids, 0)
        for field, value in self.cleaned_data.iteritems():
            if field == 'other_roles':
                result.update(
                    (int(key, 10), 1) for key in self.cleaned_data.get('other_roles', ())
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

    clone_start = forms.DateTimeField(required=True, validators=[validate_in_future],
                                      widget=JQueryDateTimePicker())
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)


class NewEventForm(forms.Form):
    start = forms.DateTimeField(required=True, validators=[validate_in_future], widget=JQueryDateTimePicker())
    duration = forms.TimeField(required=True, initial=datetime.time(hour=1))
    number_of_days = forms.IntegerField(min_value=1, max_value=31, required=True, initial=1)
    event_name = forms.CharField(min_length=1, max_length=256, required=True)
    event_template = forms.ModelChoiceField(queryset=toolkit.diary.models.EventTemplate.objects.all(), required=True)
    booked_by = forms.CharField(min_length=1, max_length=64, required=True)
    private = forms.BooleanField(required=False)
    outside_hire = forms.BooleanField(required=False)
    confirmed = forms.BooleanField(required=False)
    discounted = forms.BooleanField(required=False)


class MailoutForm(forms.Form):
    subject = forms.CharField(max_length=128, required=True)
    body = forms.CharField(required=True, widget=forms.Textarea(attrs={'wrap': 'soft', 'cols': 80}))


class SearchForm(forms.Form):
    search_term = forms.CharField(label="Search for", required=False)
    start_date = forms.DateTimeField(label="Search from", required=False)
    end_date = forms.DateTimeField(label="Search to", required=False)
    search_in_descriptions = forms.BooleanField(label="Also search event descriptions", required=False)

    def clean(self):
        cleaned_data = super(SearchForm, self).clean()

        # Check that either a search term or a searchh start or end date is supplied:
        if (len(cleaned_data.get('search_term', '').strip()) == 0
                and not
                (cleaned_data.get('start_date') or cleaned_data.get('end_date'))):
            raise forms.ValidationError("Must give either a search term or a date range")

        return cleaned_data


class NewPrintedProgrammeForm(forms.ModelForm):
    # A custom form, so as to present a month/year choice for the date (if the
    # normal Date select is used there's no trivial way to hide the choice of
    # day of month - plus this allows the available range of years to be
    # limited to Cube founding through next year)

    year = forms.ChoiceField(
        choices=[
            (y, y) for y in xrange(settings.DAWN_OF_TIME, datetime.date.today().year + 2)
        ],
        initial=datetime.date.today().year
    )
    month = forms.ChoiceField(
        choices=(zip(range(13), calendar.month_name)[1:]),
        initial=datetime.date.today().month
    )

    class Meta(object):
        model = toolkit.diary.models.PrintedProgramme

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
            raise forms.ValidationError("Invalid/missing value for year and/or month")

        self.instance.month = programme_month

        return cleaned_data


class TagForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.EventTag
        fields = ('name',)
