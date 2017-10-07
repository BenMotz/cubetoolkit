from django.conf import settings


def wagtail_content_in_menu(request):
    return {'WAGTAIL_CONTENT_IN_MENU': settings.WAGTAIL_CONTENT_IN_MENU}
