from django import forms
import toolkit.members.models


class NewMemberForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member
        fields = ('name', 'email', 'postcode')


class MemberForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member


class VolunteerForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Volunteer
        fields = ('portrait', 'notes', 'roles')
        widgets = {
            'notes': forms.Textarea(attrs={'wrap': 'soft'}),
            'roles': forms.CheckboxSelectMultiple(),
        }
