from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^programme/', include('toolkit.diary.urls')),
    url(r'^whatson/', include('toolkit.diary.urls')),
    url(r'^diary/', include('toolkit.diary.urls')),
    url(r'^auth/', include('toolkit.auth.urls')),
    # Examples:
    # url(r'^$', 'toolkit.views.home', name='home'),
    # url(r'^cube/', include('toolkit.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
