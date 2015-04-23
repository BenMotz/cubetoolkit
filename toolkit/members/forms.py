import logging
import binascii

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
import toolkit.members.models

logger = logging.getLogger(__name__)


class NewMemberForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member
        fields = ('name', 'email', 'postcode', 'is_member')
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


class DataURIImageForm(forms.Form):
    """
    Form to process PNG image data submitted as a data URI in a text field.
    """
    image_data = forms.CharField(label="", required=False, widget=forms.HiddenInput)

    def _parse_data_uri(self, image_data):
        prefix = "data:image/png;base64,"

        if not image_data.startswith(prefix):
            raise forms.ValidationError("Image data format not recognised")

        base64_data = image_data[len(prefix):]

        try:
            data = binascii.a2b_base64(base64_data)
        except (binascii.Incomplete, binascii.Error):
            logger.exception("Invalid data")
            raise forms.ValidationError("Image data could not be decoded "
                                        "(base64 data invalid)")
        return data

    def clean(self):
        cleaned_data = super(DataURIImageForm, self).clean()

        image_data_uri = cleaned_data['image_data']

        if not image_data_uri:
            # No data / empty string
            cleaned_data['image_file'] = None
            return cleaned_data

        image_data = self._parse_data_uri(image_data_uri)

        # Create a django image field, and use it to validate the uploaded
        # data:
        image_file = SimpleUploadedFile("webcam_photo.png", image_data, "image/png")
        image_field = forms.ImageField()

        cleaned_data['image_file'] = image_field.clean(image_file)

        return cleaned_data
