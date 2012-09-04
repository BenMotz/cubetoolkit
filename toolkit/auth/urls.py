from django.conf.urls import patterns, url
import django.contrib.auth.views

urlpatterns = patterns(
    'toolkit.auth.views',
    url(r'^login/$', django.contrib.auth.views.login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', django.contrib.auth.views.logout, {'template_name': 'logout.html'}, name='logout'),
)
