from django.conf import settings


def venue_longname(request):
    return {'VENUE_LONGNAME': settings.VENUE['longname']}
