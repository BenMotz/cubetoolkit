from django.conf import settings


def venue(request):
    return {'VENUE': settings.VENUE}
