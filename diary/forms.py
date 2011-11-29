from django import forms
import cube.diary.models

class DiaryIdeaForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.DiaryIdea

class EventForm(forms.ModelForm):
    class Meta(object):
        model = cube.diary.models.Event

