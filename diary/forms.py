from django import forms
import cube.diary.models

class DiaryIdeaForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.DiaryIdea

class EventForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.Event

class ShowingForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.Showing
        # Exclude these for now:
        exclude = ('event', 'extra_copy', 'extra_copy_summary', 'booked_by')


class NewShowingForm(forms.ModelForm):
    # Same as Showing, but without the role field
    class Meta(object):
        model = cube.diary.models.Showing
        # Exclude these for now:
        exclude = ('event', 'extra_copy', 'extra_copy_summary', 'booked_by', 'roles')


