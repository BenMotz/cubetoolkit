from django import forms
import cube.diary.models

class DiaryIdeaForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.DiaryIdea

class EventForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.Event
        # Ensure soft wrapping is set for textareas:
        widgets = {
                'copy': forms.Textarea(attrs={'wrap':'soft'}),
                'copy_summary': forms.Textarea(attrs={'wrap':'soft'}),
                'terms': forms.Textarea(attrs={'wrap':'soft'}),
                'notes': forms.Textarea(attrs={'wrap':'soft'}),
                  }

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


