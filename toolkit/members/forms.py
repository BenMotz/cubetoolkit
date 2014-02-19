from django import forms
import toolkit.members.models


class NewMemberForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member
        fields = ('name', 'email', 'postcode', 'mailout')
        widgets = {
                'name': forms.TextInput(attrs={'autofocus': ''}),
        }


class MemberForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member


class MemberFormWithoutNotes(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member
        exclude = ('is_member', 'notes',)


class VolunteerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VolunteerForm, self).__init__(*args, **kwargs)

        # Force ordering of roles list to be by "standard" role type, then name
        self.fields['roles'].queryset = self.fields['roles'].queryset.order_by("-standard", "name")

    class Meta(object):
        model = toolkit.members.models.Volunteer
        fields = ('portrait', 'notes', 'roles')
        widgets = {
            'notes': forms.Textarea(attrs={'wrap': 'soft'}),
            'roles': forms.CheckboxSelectMultiple(),
        }
