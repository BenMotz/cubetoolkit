from django.urls import re_path, include
import django.conf
import django.views.generic as generic
from django.views.generic.base import RedirectView
import django.views.static
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls

import toolkit.members.urls
import toolkit.toolkit_auth.urls
import toolkit.index.urls
import toolkit.diary.urls

from toolkit.index.models import IndexLink

urlpatterns = [
    re_path(r"^toolkit/admin/", admin.site.urls),
    re_path(r"^programme/", include(toolkit.diary.urls.programme_urls)),
    re_path(r"^diary/", include(toolkit.diary.urls.diary_urls)),
    re_path(r"^members/", include(toolkit.members.urls.member_urls)),
    re_path(r"^volunteers/", include(toolkit.members.urls.volunteer_urls)),
    re_path(r"^auth/", include(toolkit.toolkit_auth.urls.urlpatterns)),
    re_path(r"^toolkit/index/", include(toolkit.index.urls.urlpatterns)),
    re_path(r"^$", toolkit.diary.urls.view_diary, name="default-view"),
    re_path(
        r"^id/(?P<event_id>\d+)/$",
        toolkit.diary.urls.view_event,
        name="single-event-view",
    ),
    re_path(
        r"^robots\.txt$",
        generic.TemplateView.as_view(
            template_name="robots.txt", content_type="text/plain"
        ),
    ),
    # Archive Star and Shadow
    re_path(
        r"^on/(today|thisweek|thismonth|nextweek|nextmonth)/(.*)$",
        RedirectView.as_view(url="/", permanent=True),
        name="default-view",
    ),
    re_path(
        r"^on/(?P<year>[0-9]{4})/(.*)$",
        toolkit.diary.public_views.redirect_legacy_year,
        name="redirect-legacy-year",
    ),
    re_path(
        r"^on/(?P<event_type>\w+)/(?P<legacy_id>\d+)/$",
        toolkit.diary.public_views.redirect_legacy_event,
        name="redirect-legacy-event",
    ),
    # Main index page: requires logging in, even though some other parts
    # (eg diary index) don't.
    re_path(
        r"^toolkit/$",
        login_required(
            generic.list.ListView.as_view(
                model=IndexLink, template_name="toolkit_index.html"
            )
        ),
        name="toolkit-index",
    ),
    # Static content, only used when running in the development server
    # (django.views.static.serve only works when DEBUG=True)
    re_path(
        r"^static/(.*)$",
        django.views.static.serve,
        {"document_root": django.conf.settings.STATIC_ROOT},
    ),
    re_path(
        r"^media/(.*)$",
        django.views.static.serve,
        {"document_root": django.conf.settings.MEDIA_ROOT},
    ),
    re_path(r"^toolkit/cms/", include(wagtailadmin_urls)),
    re_path(r"^documents/", include(wagtaildocs_urls)),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    re_path(r"", include(wagtail_urls)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
