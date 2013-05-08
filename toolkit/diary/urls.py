from django.conf.urls import patterns, url
from django.views.generic import DetailView
from toolkit.diary.models import Event
from django.contrib.auth.decorators import login_required

import toolkit.diary.feeds
from toolkit.diary.public_views import ArchiveIndex, ArchiveYear, ArchiveMonth


urlpatterns = patterns(
    'toolkit.diary.public_views',

    # View lists of event for various time/dates
    url('^(?:view/|)$', 'view_diary', name="default-view"),
    url('^view/(?P<year>\d{4})/?$', 'view_diary', name="year-view"),
    url('^view/(?P<year>\d{4})/(?P<month>\d{1,2})/?$', 'view_diary', name="month-view"),
    url('^view/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/?$', 'view_diary', name="day-view"),
    # View for events by tag. This needs to come *after* the year view, to
    # avoid years being parsed as tags:
    url('^view/(?P<event_type>[\w-]+)/$', 'view_diary', name="type-view"),

    # View individual showing
    url('^showing/id/(?P<showing_id>\d+)/$', 'view_showing', name="single-showing-view"),
    # All showings for a given event
    url('^event/id/(?P<event_id>\d+)/$', 'view_event', name="single-event-view"),
    # As above, for legacy event ID:
    url('^event/oldid/(?P<legacy_id>\d+)/$', 'view_event', name="single-event-view-legacyid"),

    # Archive:
    url('^archive/$', ArchiveIndex.as_view(), name="archive-view-index"),
    url('^archive/(?P<year>\d{4})/$', ArchiveYear.as_view(), name="archive-view-year"),
    url('^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/$', ArchiveMonth.as_view(), name="archive-view-month"),

    # Get JSON describing events on a given (single) date:
    url('^view/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/json$', 'view_diary_json', name="day-view-json"),

    # RSS feed
    url('^rss/$', toolkit.diary.feeds.BasicWhatsOnFeed(), name="view-diary-rss", ),
)

urlpatterns += patterns(
    'toolkit.diary.edit_views',

    # View lists of events for editing:
    url('^edit/?$', 'edit_diary_list', name="default-edit", ),
    url('^edit/(?P<year>\d{4})/?$', 'edit_diary_list', name="year-edit", ),
    url('^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/?$', 'edit_diary_list', name="month-edit", ),
    url('^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})', 'edit_diary_list', name="day-edit", ),

    # Edit an event: view event before editing
    url('^edit/event/id/(?P<pk>\d+)/view/$',
        login_required(DetailView.as_view(
            model=Event,
            template_name='view_event_privatedetails.html')), name="edit-event-details-view"
        ),
    # Edit an event
    url('^edit/event/id/(?P<event_id>\d+)/$', 'edit_event', name="edit-event-details"),
    # Edit a showing (includes delete / add a new showing)
    url('^edit/showing/id/(?P<showing_id>\d+)/$', 'edit_showing', name="edit-showing"),
    # Edit ideas
    url('^edit/ideas/(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'edit_ideas', name="edit-ideas"),
    # Add a new showing (to an existing event) - submission URL for edit-showing
    url('^edit/event/id/(?P<event_id>\d+)/addshowing$', 'add_showing', name="add-showing"),
    # Delete a showing
    url('^edit/showing/id/(?P<showing_id>\d+)/delete$', 'delete_showing', name="delete-showing"),
    # Add a new event + showing
    url('^edit/event/add$', 'add_event', name="add-event"),

    # Edit event types
    url('^edit/eventtemplates/', 'edit_event_templates', name='edit_event_templates'),
    url('^edit/eventtags/', 'edit_event_tags', name='edit_event_tags'),

    # Edit event roles
    url('^edit/roles/', 'edit_roles', name='edit_roles'),

    # The slightly OTT regex in the following will match:
    # "rota" "rota/" "rota/2001/01" "rota/2001/01/" "rota/2001/1/02" "rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    # View rota
    url("""^(?P<field>rota|copy|terms)(/|/(?P<year>\d{4})/(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$""",
        'view_event_field', name="view_event_field"),

    url("^mailout/$", 'mailout', name="members-mailout"),
    url("^mailout/send$", 'exec_mailout', name="exec-mailout"),
    url("^mailout/send/progress$", 'mailout_progress', name="mailout-progress"),

    # Ajax calls:
    url("^edit/setprefs$", 'set_edit_preferences', name="set_edit_preferences"),
)
