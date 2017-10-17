from django.conf import settings
from toolkit.diary.models import EventTag


def venue(request):
    return {'VENUE': settings.VENUE}


def event_tags(request):
    return {'EVENT_TAGS': EventTag.objects.all()}
