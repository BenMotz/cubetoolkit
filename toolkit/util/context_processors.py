from django.conf import settings


def venue(request):
    return {
        "VENUE": settings.VENUE,
        "membership_expiry_enabled": settings.MEMBERSHIP_EXPIRY_ENABLED,
    }
