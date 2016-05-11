from django.conf.urls import patterns, include, url
import django.conf
import django.views.generic as generic
from django.contrib.auth.decorators import login_required

import toolkit.members.urls
import toolkit.toolkit_auth.urls
import toolkit.index.urls
import toolkit.diary.urls
import toolkit.about.urls

from toolkit.index.models import IndexLink

urlpatterns = patterns(
    '',
    url(r'^programme/', include(toolkit.diary.urls.programme_urls)),
    url(r'^diary/', include(toolkit.diary.urls.diary_urls)),
    url(r'^members/', include(toolkit.members.urls.member_urls)),
    url(r'^volunteers/', include(toolkit.members.urls.volunteer_urls)),
    url(r'^auth/', include(toolkit.toolkit_auth.urls.urlpatterns)),
    url(r'^index/', include(toolkit.index.urls.urlpatterns)),
    url(r'^about/', include(toolkit.about.urls.about_urls)),

    # Main index page: requires logging in, even though some other parts
    # (eg diary index) don't.
    url(r'^$', login_required(
        generic.list.ListView.as_view(
            model=IndexLink,
            template_name='toolkit_index.html')
        ),
        name="toolkit-index"),

    # Static content, only used when running in the development server
    # (django.views.static.serve only works when DEBUG=True)
    url(r'^static/(.*)$', 'django.views.static.serve', {'document_root': django.conf.settings.STATIC_ROOT}),
    url(r'^media/(.*)$', 'django.views.static.serve', {'document_root': django.conf.settings.MEDIA_ROOT}),
)
