from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns( 'cube.diary.views',
    # View lists of event for various time/dates
    url('^$', 'view_diary', name="default-view"),
    url('^(?P<year>\d{4})$', 'view_diary', name="year-view"),
    url('^(?P<year>\d{4})/(?P<month>\d{1,2})$', 'view_diary', name="month-view"),
    url('^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})', 'view_diary', name="day-view"),

    # As above, but lists of events for editing:
    url('^edit/?$', 'edit_diary_list', name="default-edit", ),
    url('^edit/(?P<year>\d{4})$', 'edit_diary_list', name="year-edit", ),
    url('^edit/(?P<year>\d{4})/(?P<month>\d{1,2})$', 'edit_diary_list', name="month-edit", ),
    url('^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})', 'edit_diary_list', name="day-edit", ),

    # Edit individual showings / events:
    url('^edit/event/id/(?P<event_id>\d+)$', 'edit_event', name="edit-event-details"),
#    url('^edit/event/id/(?P<event_id>\d+)/showings$', 'edit_showings', name="edit-event-showings"),
    url('^edit/showing/id/(?P<showing_id>\d+)$', 'edit_showing', name="edit-showing"),
    url('^edit/ideas/(?P<year>\d{4})/(?P<month>\d{1,2})$', 'edit_ideas', name="edit-ideas"),

     url('^add/event/id/(?P<event_id>\d+)/showing$', 'add_showing', name="add-showing"),

#    url('^edit/event/new$', 'new_event'

    # View individual showing
    url('^showing/id/(?P<showing_id>\d+)$', 'view_showing', name="single-showing-view"),
    # All showings for a given event
    url('^event/id/(?P<event_id>\d+)$', 'view_event', name="single-event-view"),

    # Delete things
    url('^edit/showing/id/(?P<showing_id>\d+)/delete$', 'delete_showing', name="delete-showing"),
)

