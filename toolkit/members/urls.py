from django.conf.urls.defaults import patterns, url

# Volunteers:
volunteer_urls = patterns('toolkit.members.views',
    url('^add$', 'add_volunteer', name='add-volunteer'),
    url('^search$', 'search', name='search-volunteers', kwargs={ 'volunteers' : True } ),
    url('^view$', 'view_list', name='view-volunteer-list', kwargs={ 'volunteers' : True } ),
    url('^(?P<member_id>\d+)$', 'view', name='view-volunteer', kwargs={ 'volunteers' : True } ),
    url('^(?P<member_id>\d+)/edit$', 'edit_volunteer', name='edit-volunteer'),
    url('^(?P<member_id>\d+)/delete$', 'delete_volunteer', name='delete-volunteer'),
)

# Members:
member_urls = patterns('toolkit.members.views',
    url('^add$', 'add_member', name='add-member'),
    url('^search$', 'search', name='search-members'),
    url('^view$', 'view_list', name='view-member-list'),
    url('^(?P<member_id>\d+)$', 'view', name='view-member'),
    url('^(?P<member_id>\d+)/edit$', 'edit_member', name='edit-member'),
    url('^(?P<member_id>\d+)/delete$', 'delete_member', name='delete-member'),
    url('^statistics$', 'member_statistics', name='member-statistics'),
)
