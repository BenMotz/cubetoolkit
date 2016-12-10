from django.conf.urls import url

from toolkit.members.volunteer_views import (
    view_volunteer_list,
    view_volunteer_role_report, edit_volunteer, select_volunteer,
    activate_volunteer)

from toolkit.members.member_views import (
    add_member, search, view,
    edit_member, delete_member, member_statistics, member_homepages,
    unsubscribe_member)

# Volunteers:
volunteer_urls = [
    url(r'^$', view_volunteer_list),
    url(r'^add/$', edit_volunteer,
        name='add-volunteer',
        kwargs={'volunteer_id': None, 'create_new': True}),
    url(r'^view/$', view_volunteer_list,
        name='view-volunteer-list'),
    url(r'^view/rolereport/$', view_volunteer_role_report,
        name='view-volunteer-role-report'),
    url(r'^retire/select$', select_volunteer,
        name='retire-select-volunteer',
        kwargs={'action': 'retire'}),
    url(r'^unretire/select$', select_volunteer,
        name='unretire-select-volunteer',
        kwargs={'action': 'unretire', 'active': False}),

    url(r'^(?P<volunteer_id>\d+)/edit$', edit_volunteer,
        name='edit-volunteer'),

    url(r'^unretire$', activate_volunteer,
        name='activate-volunteer'),
    url(r'^retire$', activate_volunteer,
        name='inactivate-volunteer',
        kwargs={'set_active': False}),
]

# Members:
member_urls = [
    # Internal:
    url(r'^add/$', add_member,
        name='add-member'),
    url(r'^search/$', search,
        name='search-members'),
    url(r'^(?P<member_id>\d+)$', view,
        name='view-member'),
    url(r'^(?P<member_id>\d+)/edit/$', edit_member,
        name='edit-member'),
    url(r'^(?P<member_id>\d+)/delete$', delete_member,
        name='delete-member'),
    url(r'^statistics/$', member_statistics,
        name='member-statistics'),

    # External:
    url(r'^homepages/$', member_homepages,
        name='member-homepages'),

    # Semi-external (see member_views.py for details)
    url(r'^(?P<member_id>\d+)/edit/$', edit_member,
        name='edit-member'),
    url(r'^(?P<member_id>\d+)/unsubscribe/$', unsubscribe_member,
        name='unsubscribe-member'),
]
