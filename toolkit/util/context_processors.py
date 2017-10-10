from django.conf import settings


def venue_longname(request):
    return {'VENUE_LONGNAME': settings.VENUE['longname']}


def venue_int_header_img(request):
    return {'VENUE_HEADER_IMG': settings.VENUE['internal_header_img']}
