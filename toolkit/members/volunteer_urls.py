from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('toolkit.members.views',
    url('^search$', 'search', name='search-volunteers', kwargs={ 'volunteers' : True } ),
    url('^view$', 'view_list', name='view-volunteer-list', kwargs={ 'volunteers' : True } ),
    url('^(?P<member_id>\d+)$', 'view', name='view-volunteer', kwargs={ 'volunteers' : True } ),
    url('^(?P<member_id>\d+)/edit$', 'edit_volunteer', name='edit-volunteer'),
)

