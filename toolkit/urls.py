from django.urls import re_path, include
import django.conf
import django.views.generic as generic
import django.views.static
from django.contrib.auth.decorators import login_required
from django.conf import settings

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls

import toolkit.members.urls
import toolkit.toolkit_auth.urls
import toolkit.index.urls
import toolkit.diary.urls

from toolkit.index.models import IndexLink

urlpatterns = [
    re_path(r"^programme/", include(toolkit.diary.urls.programme_urls)),
    re_path(r"^diary/", include(toolkit.diary.urls.diary_urls)),
    re_path(r"^members/", include(toolkit.members.urls.member_urls)),
    re_path(r"^volunteers/", include(toolkit.members.urls.volunteer_urls)),
    re_path(r"^auth/", include(toolkit.toolkit_auth.urls.urlpatterns)),
    re_path(r"^index/", include(toolkit.index.urls.urlpatterns)),
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
    re_path(r"^cms/", include(wagtailadmin_urls)),
    re_path(r"^doc/", include(wagtaildocs_urls)),
    re_path(r"^pages/", include(wagtail_urls)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
