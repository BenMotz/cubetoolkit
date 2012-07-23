import datetime
from django import forms
import django.db.models
from django.conf import settings

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
            'copy': forms.Textarea(attrs={'wrap': 'soft'}),
            'copy_summary': forms.Textarea(attrs={'wrap': 'soft'}),
            'terms': forms.Textarea(attrs={'wrap': 'soft'}),
            'notes': forms.Textarea(attrs={'wrap': 'soft'}),
        }
        order = ('tags', )
        fields = ('name', 'tags', 'duration', 'cancelled', 'outside_hire',
                  'private', 'copy', 'copy_summary', 'terms', 'notes')


class MediaItemForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.MediaItem
        widgets = {
            'media_file': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/gif,image/png'}),
        }
        exclude = ('thumbnail', 'mimetype', 'caption')


class ShowingForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Showing
        # Exclude these for now:
        exclude = ('event', 'extra_copy', 'extra_copy_summary', 'roles')


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
            members["role_{0}".format(role.pk)] = (
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

    clone_start = forms.DateTimeField(required=True, validators=[validate_in_future])
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)


class NewEventForm(forms.Form):
    start = forms.DateTimeField(required=True, validators=[validate_in_future])
    start = forms.DateTimeField(required=True)
    duration = forms.TimeField(required=True, initial=datetime.time(hour=1))
    number_of_days = forms.IntegerField(min_value=1, max_value=31, required=True, initial=1)
    event_name = forms.CharField(min_length=3, max_length=128, required=True)
    event_template = forms.ModelChoiceField(queryset=toolkit.diary.models.EventTemplate.objects.all(), required=False)
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)
    private = forms.BooleanField(required=False)
    external = forms.BooleanField(required=False)
    confirmed = forms.BooleanField(required=False)
    discounted = forms.BooleanField(required=False)


class MailoutForm(forms.Form):
    subject = forms.CharField(max_length=128, required=True)
    body = forms.CharField(required=True, widget=forms.Textarea(attrs={'wrap': 'soft', 'cols': 80}))
