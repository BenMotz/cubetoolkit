import datetime
from django import forms
import toolkit.diary.models

class DiaryIdeaForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.DiaryIdea

class EventForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Event
        # Ensure soft wrapping is set for textareas:
        widgets = {
                'copy': forms.Textarea(attrs={'wrap':'soft'}),
                'copy_summary': forms.Textarea(attrs={'wrap':'soft'}),
                'terms': forms.Textarea(attrs={'wrap':'soft'}),
                'notes': forms.Textarea(attrs={'wrap':'soft'}),
                  }

class ShowingForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.diary.models.Showing
        # Exclude these for now:
        exclude = ('event', 'extra_copy', 'extra_copy_summary')


class NewShowingForm(forms.ModelForm):
    # Same as Showing, but without the role field
    class Meta(object):
        model = toolkit.diary.models.Showing
        # Exclude these for now:
        exclude = ('event', 'extra_copy', 'extra_copy_summary', 'roles')

class NewEventForm(forms.Form):
    start = forms.DateTimeField(required=True)
    duration = forms.TimeField(required=True, initial=datetime.time(hour=1))
    number_of_days = forms.IntegerField(min_value=1, max_value=31, required=True, initial=1)
    event_name = forms.CharField(min_length=3, max_length=128, required=True)
    event_type = forms.ModelChoiceField(queryset=toolkit.diary.models.EventType.objects.all(), required=False)
    booked_by = forms.CharField(min_length=1, max_length=128, required=True)
    private = forms.BooleanField(required=False)
    external = forms.BooleanField(required=False)
    confirmed = forms.BooleanField(required=False)
    discounted = forms.BooleanField(required=False)


