from django.conf.urls.defaults import patterns, url

urlpatterns = patterns( 'toolkit.auth.views',
    url('^login/(?P<atype>[a-z,]+)$', 'auth', name="auth"),
    url('^logout$', 'clear_auth', name="logout"),
)

