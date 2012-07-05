from django.conf.urls import patterns, url

# Volunteers:
volunteer_urls = patterns('toolkit.members.volunteer_views',
    url('^$', 'view_volunteer_list'),
    url('^add/$', 'edit_volunteer', name='add-volunteer', kwargs={ 'member_id' : None, 'create_new' : True}),
    url('^view/$', 'view_volunteer_list', name='view-volunteer-list'),
    url('^select$', 'select_volunteer', name='select-volunteer'),
    url('^select/inactive$', 'select_volunteer', name='select-volunteer-inactive', kwargs={'active' : False}),

    url('^(?P<member_id>\d+)/edit$', 'edit_volunteer', name='edit-volunteer'),

    url('^active/set$', 'activate_volunteer', name='activate-volunteer'),
    url('^active/unset$', 'activate_volunteer', name='inactivate-volunteer', kwargs={'active' : False}),
)

# Members:
member_urls = patterns('toolkit.members.member_views',
    # Internal:
    url('^add/$', 'add_member', name='add-member'),
    url('^search/$', 'search', name='search-members'),
    url('^(?P<member_id>\d+)$', 'view', name='view-member'),
    url('^(?P<member_id>\d+)/edit/$', 'edit_member', name='edit-member'),
    url('^(?P<member_id>\d+)/delete$', 'delete_member', name='delete-member'),
    url('^statistics/$', 'member_statistics', name='member-statistics'),

    # External:
    url('^homepages/$', 'member_homepages', name='member-homepages'),
)
