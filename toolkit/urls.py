from django.conf.urls import include, url
import django.conf
import django.views.generic as generic
import django.views.static
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.core import urls as wagtail_urls

import toolkit.members.urls
import toolkit.toolkit_auth.urls
import toolkit.index.urls
import toolkit.diary.urls

from toolkit.index.models import IndexLink

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^programme/", include(toolkit.diary.urls.programme_urls)),
    url(r"^diary/", include(toolkit.diary.urls.diary_urls)),
    url(r"^members/", include(toolkit.members.urls.member_urls)),
    url(r"^volunteers/", include(toolkit.members.urls.volunteer_urls)),
    url(r"^auth/", include(toolkit.toolkit_auth.urls.urlpatterns)),
    url(r"^index/", include(toolkit.index.urls.urlpatterns)),
    url(r"^$", toolkit.diary.urls.view_diary, name="default-view"),
    url(
        r"^id/(?P<event_id>\d+)/$",
        toolkit.diary.urls.view_event,
        name="single-event-view",
    ),
    url(
        r"^robots\.txt$",
        generic.TemplateView.as_view(
            template_name="robots.txt", content_type="text/plain"
        ),
    ),
    # Main index page: requires logging in, even though some other parts
    # (eg diary index) don't.
    url(
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
    url(
        r"^static/(.*)$",
        django.views.static.serve,
        {"document_root": django.conf.settings.STATIC_ROOT},
    ),
    url(
        r"^media/(.*)$",
        django.views.static.serve,
        {"document_root": django.conf.settings.MEDIA_ROOT},
    ),
    url(r"^cms/", include(wagtailadmin_urls)),
    url(r"^documents/", include(wagtaildocs_urls)),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r"^pages/", include(wagtail_urls)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
