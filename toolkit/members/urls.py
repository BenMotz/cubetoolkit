from django.conf.urls import patterns, url

# Volunteers:
volunteer_urls = patterns(
    'toolkit.members.volunteer_views',
    url('^$', 'view_volunteer_list'),
    url('^add/$', 'edit_volunteer', name='add-volunteer', kwargs={'member_id': None, 'create_new': True}),
    url('^view/$', 'view_volunteer_list', name='view-volunteer-list'),
    url('^retire/select$', 'select_volunteer', name='retire-select-volunteer', kwargs={'action': 'retire'}),
    url('^unretire/select$', 'select_volunteer', name='unretire-select-volunteer', kwargs={'action': 'unretire', 'active': False}),

    url('^(?P<member_id>\d+)/edit$', 'edit_volunteer', name='edit-volunteer'),

    url('^unretire$', 'activate_volunteer', name='activate-volunteer'),
    url('^retire$', 'activate_volunteer', name='inactivate-volunteer', kwargs={'set_active': False}),
)

# Members:
member_urls = patterns(
    'toolkit.members.member_views',
    # Internal:
    url('^add/$', 'add_member', name='add-member'),
    url('^search/$', 'search', name='search-members'),
    url('^(?P<member_id>\d+)$', 'view', name='view-member'),
    url('^(?P<member_id>\d+)/edit/$', 'edit_member', name='edit-member'),
    url('^(?P<member_id>\d+)/delete$', 'delete_member', name='delete-member'),
    url('^statistics/$', 'member_statistics', name='member-statistics'),

    # External:
    url('^homepages/$', 'member_homepages', name='member-homepages'),

    # Semi-external (see member_views.py for details)
    url('^(?P<member_id>\d+)/edit/$', 'edit_member', name='edit-member'),
    url('^(?P<member_id>\d+)/unsubscribe/$', 'unsubscribe_member', name='unsubscribe-member'),
)
