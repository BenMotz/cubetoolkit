from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns( 'cube.diary.views',
    # View lists of event for various time/dates
    url('^$', 'view_diary', name="default-view"),
    url('^(?P<year>\d{4})$', 'view_diary', name="year-view"),
    url('^(?P<year>\d{4})/(?P<month>\d{1,2})$', 'view_diary', name="month-view"),
    url('^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})', 'view_diary', name="day-view"),

    # As above, but editing:
    url('^edit$', 'view_diary', name="default-edit", kwargs = { 'edit' : True}),
    url('^edit/(?P<year>\d{4})$', 'view_diary', name="year-edit", kwargs = { 'edit' : True}),
    url('^edit/(?P<year>\d{4})/(?P<month>\d{1,2})$', 'view_diary', name="month-edit", kwargs = { 'edit' : True}),
    url('^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})', 'view_diary', name="day-edit", kwargs = { 'edit' : True}),

    # Individual showing
    url('^showing/id/(?P<showing_id>\d+)$', 'view_showing', name="single-showing-view"),
    # All showings for a given event
    url('^event/id/(?P<event_id>\d+)$', 'view_event', name="single-event-view"),
)

