import datetime

from django.core.exceptions import ValidationError


def validate_in_future(time):
    # XXX: Should probably be working in UTC?
    if time < datetime.datetime.now():
        raise ValidationError('Must be in the future')
