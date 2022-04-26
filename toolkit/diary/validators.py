from django.core.exceptions import ValidationError
import django.utils.timezone


def validate_in_future(time):
    # Use d.u.t.now() instead of datetime.now as the django version returns
    # a datetime object with the timezone set (to UTC) so the comparison will
    # be correct for summertime, etc.
    if time < django.utils.timezone.now():
        raise ValidationError("Must be in the future")
