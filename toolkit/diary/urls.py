from django.conf.urls import patterns, url
from django.views.generic import DetailView
from toolkit.diary.models import Event
from django.contrib.auth.decorators import permission_required

import toolkit.diary.feeds
from toolkit.diary.edit_views import EditEventView, EditRotaView
from toolkit.diary.public_views import (ArchiveIndex, ArchiveYear,
                                        ArchiveMonth, ArchiveSearch)


programme_urls = patterns(
    'toolkit.diary.public_views',

    # View lists of event for various time/dates
    url(r'^(?:view/|)$', 'view_diary', name="default-view"),
    url(r'^view/(?P<year>\d{4})/?$', 'view_diary', name="year-view"),
    url(r'^view/(?P<year>\d{4})/(?P<month>\d{1,2})/?$', 'view_diary', name="month-view"),
    url(r'^view/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/?$', 'view_diary', name="day-view"),

    url(r'^view/this_week$', 'view_diary_this_week', name="view-this-week"),
    url(r'^view/next_week$', 'view_diary_next_week', name="view-next-week"),
    url(r'^view/this_month$', 'view_diary_this_month', name="view-this-month"),
    url(r'^view/next_month$', 'view_diary_next_month', name="view-next-month"),

    # View for events by tag. This needs to come *after* the year view, to
    # avoid years being parsed as tags:
    url(r'^view/(?P<event_type>[\w-]+)/$', 'view_diary', name="type-view"),

    # View individual showing
    url(r'^showing/id/(?P<showing_id>\d+)/$', 'view_showing', name="single-showing-view"),
    # All showings for a given event
    url(r'^event/id/(?P<event_id>\d+)/$', 'view_event', name="single-event-view"),
    url(r'^event/(?P<event_slug>[\w\-_]*),(?P<event_id>\d+)/$', 'view_event', name="single-event-view-with-slug"),
    # As above, for legacy event ID:
    url(r'^event/oldid/(?P<legacy_id>\d+)/$', 'view_event', name="single-event-view-legacyid"),

    # Archive:
    url(r'^archive/$', ArchiveIndex.as_view(), name="archive-view-index"),
    url(r'^archive/(?P<year>\d{4})/$', ArchiveYear.as_view(), name="archive-view-year"),
    url(r'^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/$', ArchiveMonth.as_view(), name="archive-view-month"),
    # Search
    url(r'^archive/search/$', ArchiveSearch.as_view(), name="archive-search"),

    # Get JSON describing events on a given (single) date:
    url(r'^view/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/json$', 'view_diary_json', name="day-view-json"),

    # RSS feed
    url(r'^rss/$', toolkit.diary.feeds.BasicWhatsOnFeed(), name="view-diary-rss", ),
)

diary_urls = patterns(
    'toolkit.diary.edit_views',

    # Used for cancelling an edit action:
    url(r'^edit/cancel/?$', 'cancel_edit', name="cancel-edit", ),

    # View lists of events for editing:
    url(r'^edit/?$', 'edit_diary_list', name="default-edit", ),
    url(r'^edit/(?P<year>\d{4})/?$', 'edit_diary_list', name="year-edit", ),
    url(r'^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/?$', 'edit_diary_list', name="month-edit", ),
    url(r'^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})', 'edit_diary_list', name="day-edit", ),

    # Edit an event: view event before editing
    url(r'^edit/event/id/(?P<pk>\d+)/view/$',
        permission_required('toolkit.read')(DetailView.as_view(
            model=Event,
            template_name='view_event_privatedetails.html')), name="edit-event-details-view"
        ),
    # Edit an event
    url(r'^edit/event/id/(?P<event_id>\d+)/$', EditEventView.as_view(), name="edit-event-details"),
    # Edit a showing (includes delete / add a new showing)
    url(r'^edit/showing/id/(?P<showing_id>\d+)/$', 'edit_showing', name="edit-showing"),
    # Edit rota notes for a showing
    url(r'^edit/showing/id/(?P<showing_id>\d+)/rota_notes/$', 'edit_showing_rota_notes', name="edit-showing-rota-notes"),
    # Edit ideas
    url(r'^edit/ideas/(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'edit_ideas', name="edit-ideas"),
    # Add a new showing (to an existing event) - submission URL for edit-showing
    url(r'^edit/event/id/(?P<event_id>\d+)/addshowing$', 'add_showing', name="add-showing"),
    # Delete a showing
    url(r'^edit/showing/id/(?P<showing_id>\d+)/delete$', 'delete_showing', name="delete-showing"),
    # Add a new event + showing
    url(r'^edit/event/add$', 'add_event', name="add-event"),

    # Edit event types
    url(r'^edit/eventtemplates/', 'edit_event_templates', name='edit_event_templates'),
    url(r'^edit/eventtags/', 'edit_event_tags', name='edit_event_tags'),

    # Edit event roles
    url(r'^edit/roles/', 'edit_roles', name='edit_roles'),

    # The slightly OTT regex in the following will match:
    # "rota" "rota/" "rota/2001/01" "rota/2001/01/" "rota/2001/1/02" "rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    # View rota
    url(r"""^(?P<field>rota|copy|terms|copy_summary)(/|/(?P<year>\d{4})/(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$""",
        'view_event_field', name="view_event_field"),

    # As above, will match:
    # "edit/rota" "edit/rota/" "edit/rota/2001/01" "edit/rota/2001/01/"
    # "edit/rota/2001/1/02" "edit/rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    url(r"^edit/rota(/|/(?P<year>\d{4})/(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$$",
        EditRotaView.as_view(), name="rota-edit"),

    url(r"^rota/vacancies$", 'view_rota_vacancies', name="view-rota-vacancies"),

    # Ajax calls:
    url("^edit/setprefs$", 'set_edit_preferences', name="set_edit_preferences"),

    # Printed programme archive edit/upload:
    url("^printedprogrammes$", 'printed_programme_edit', name="edit-printed-programmes", kwargs={'operation': 'edit'}),
    url("^printedprogrammes/add$", 'printed_programme_edit', name="add-printed-programme", kwargs={'operation': 'add'}),

    # Force a 500 error, to test error emailing
    url(r'error/$', 'view_force_error'),
)

diary_urls += patterns(
    'toolkit.diary.mailout_views',

    url("^mailout/$", 'mailout', name="members-mailout"),
    url("^mailout/send$", 'exec_mailout', name="exec-mailout"),
    url("^mailout/send/progress$", 'mailout_progress', name="mailout-progress"),
)
