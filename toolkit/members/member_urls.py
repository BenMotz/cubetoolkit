from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('toolkit.members.views',
    url('^search$', 'search', name='search-members'),
    url('^view$', 'view_list', name='view-member-list'),
    url('^(?P<member_id>\d+)$', 'view', name='view-member'),
    url('^(?P<member_id>\d+)/edit$', 'edit_member', name='edit-member'),
)

