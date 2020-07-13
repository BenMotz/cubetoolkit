import logging
import binascii
import datetime

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from toolkit.members.models import Member, TrainingRecord
import toolkit.diary.models
from toolkit.diary.form_widgets import ChosenSelectMultiple
from django.conf import settings

logger = logging.getLogger(__name__)


class NewMemberForm(forms.ModelForm):
    class Meta(object):
        model = toolkit.members.models.Member
        fields = ('name', 'email', 'postcode', 'is_member')
        widgets = {
            'name': forms.TextInput(attrs={'autofocus': ''}),
        }


class MemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        hide_internal_fields = kwargs.pop('hide_internal_fields', True)
        super(MemberForm, self).__init__(*args, **kwargs)

        if not settings.MEMBERSHIP_EXPIRY_ENABLED or hide_internal_fields:
            del self.fields['membership_expires']
        if hide_internal_fields:
            del self.fields['is_member']
            del self.fields['mailout_failed']
        del self.fields['gdpr_opt_in']

    class Meta(object):
        model = toolkit.members.models.Member
        exclude = ()


class MemberFormWithoutNotes(forms.ModelForm):
    # Specify prefix to allow this to coexist in a single <form> alongside
    # VolunteerForm
    prefix = "mem"

    class Meta(object):
        model = toolkit.members.models.Member
        exclude = ('is_member', 'notes', 'mailout_failed',
                   'membership_expires', 'gdpr_opt_in')


class VolunteerForm(forms.ModelForm):
    # Extra non-model field. If this is returned with a base64 encoded PNG data
    # URI then this is saved as the volunteer portrait.
    image_data = forms.CharField(label="", required=False,
                                 widget=forms.HiddenInput)

    # Specify prefix to allow this to coexist in a single <form> alongside
    # MemberFormWithoutNotes
    prefix = "vol"

    def __init__(self, *args, **kwargs):
        super(VolunteerForm, self).__init__(*args, **kwargs)

        # Force ordering of roles list to be by "standard" role type, then name
        self.fields['roles'].queryset = (
            self.fields['roles'].queryset.order_by("-standard", "name"))

    class Meta(object):
        model = toolkit.members.models.Volunteer
        fields = ('portrait', 'notes', 'roles')
        widgets = {
            'notes': forms.Textarea(attrs={'wrap': 'soft'}),
            'roles': forms.CheckboxSelectMultiple(),
        }

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
        # Try to extract a photo from the image_data field. If successful, save
        # as the portrait. Note that the image will be used in preference to
        # any uploaded file, and will result in the 'clear' checkbox being
        # ignored. This is intentional, as the photo is harder to replace than
        # the uploaded image, if someone's managed to do both.

        cleaned_data = super(VolunteerForm, self).clean()

        image_data_uri = cleaned_data['image_data']

        if image_data_uri:
            image_data = self._parse_data_uri(image_data_uri)
            image_file = SimpleUploadedFile("webcam_photo.png",
                                            image_data, "image/png")
            # Use portrait field to validate the uploaded data:
            cleaned_data['portrait'] = (
                self.fields['portrait'].clean(image_file))

        return cleaned_data


class TrainingRecordForm(forms.ModelForm):
    class Meta(object):
        model = TrainingRecord
        fields = ('training_type', 'role', 'trainer', 'training_date', 'notes')


class GroupTrainingForm(forms.Form):
    type = forms.ChoiceField(
        choices=TrainingRecord.TRAINING_TYPE_CHOICES,
        required=True)
    role = forms.ModelChoiceField(
        queryset=toolkit.diary.models.Role.objects.all(),
        required=False)
    training_date = forms.DateField(
        required=True, initial=datetime.date.today)
    trainer = forms.CharField(
        min_length=2, max_length=128, required=True)
    volunteers = forms.ModelMultipleChoiceField(
        queryset=Member.objects.filter(volunteer__active=True)
        .order_by('name'),
        widget=ChosenSelectMultiple(width="100%"),
        required=True)
    notes = forms.CharField(
        widget=forms.Textarea, required=False,
        help_text="(will be added to all selected volunteer's training "
        "records)")

    def clean(self):
        super(GroupTrainingForm, self).clean()
        if (self.cleaned_data.get("type") == TrainingRecord.ROLE_TRAINING
                and self.cleaned_data.get("role") is None):
            self.add_error("role", "This field is required.")
