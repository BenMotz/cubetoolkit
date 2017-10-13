from django.conf import settings


def diary_settings(request):
    return {'MULTIROOM_ENABLED': settings.MULTIROOM_ENABLED}
