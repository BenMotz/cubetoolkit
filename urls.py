import cube.settings
from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^programme/', include('cube.diary.urls')),
    url(r'^whatson/', include('cube.diary.urls')),
    url(r'^diary/', include('cube.diary.urls')),
    url(r'^auth/', include('cube.auth.urls')),
    # Examples:
    # url(r'^$', 'cube.views.home', name='home'),
    # url(r'^cube/', include('cube.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^static/(.*)$', 'django.views.static.serve',{'document_root':cube.settings.STATIC_ROOT}),

)
