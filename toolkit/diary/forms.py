import datetime
from django import forms
from django.core.exceptions import ValidationError
import toolkit.diary.models


def _in_past(time):
    # XXX: Should probably be working in UTC?
    return time < datetime.datetime.now()


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
        exclude = ('event', 'extra_copy', 'extra_copy_summary')

    def clean_start(self):
        start = self.cleaned_data['start']
        if _in_past(start):
            raise ValidationError("May not be in the past")
        else:
            return start


class CloneShowingForm(forms.Form):
    # For cloning a showing, so only need very minimal extra details
    start = forms.DateTimeField(required=True)
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)

    def clean_start(self):
        if _in_past(self.cleaned_data['start']):
            raise ValidationError("May not be in the past")

class NewEventForm(forms.Form):
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

    def clean_start(self):
        if _in_past(self.cleaned_data['start']):
            raise ValidationError("May not be in the past")

class MailoutForm(forms.Form):
    subject = forms.CharField(max_length=128, required=True)
    body = forms.CharField(required=True, widget=forms.Textarea(attrs={'wrap': 'soft', 'cols': 80}))
