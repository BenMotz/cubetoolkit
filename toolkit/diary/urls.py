from django.conf.urls import url
from toolkit.diary.models import Event
from django.contrib.auth.decorators import permission_required

import toolkit.diary.feeds
from toolkit.diary.edit_views import (
    EditEventView,
    EditRotaView,
    event_detail_view,
    cancel_edit,
    edit_diary_list,
    edit_diary_calendar,
    edit_diary_data,
    edit_showing,
    edit_showing_rota_notes,
    edit_ideas,
    delete_showing,
    add_event,
    edit_event_templates,
    edit_event_tags,
    edit_roles,
    view_event_field,
    view_rota_vacancies,
    set_edit_preferences,
    get_messages,
    printed_programme_edit,
    view_force_error,
)
from toolkit.diary.public_views import (
    ArchiveIndex,
    ArchiveYear,
    ArchiveMonth,
    ArchiveSearch,
    view_diary,
    view_diary_this_week,
    view_diary_next_week,
    view_diary_this_month,
    view_diary_next_month,
    view_showing,
    view_event,
)

from toolkit.diary.mailout_views import (
    mailout,
    exec_mailout,
    mailout_progress,
    mailout_test_send,
)


programme_urls = [
    # View lists of event for various time/dates
    url(r"^(?:view/)?$", view_diary, name="programme-view"),
    url(r"^view/(?P<year>\d{4})/?$", view_diary, name="year-view"),
    url(
        r"^view/(?P<year>\d{4})/(?P<month>\d{1,2})/?$",
        view_diary,
        name="month-view",
    ),
    url(
        r"^view/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/?$",
        view_diary,
        name="day-view",
    ),
    url(r"^view/this_week$", view_diary_this_week, name="view-this-week"),
    url(r"^view/next_week$", view_diary_next_week, name="view-next-week"),
    url(r"^view/this_month$", view_diary_this_month, name="view-this-month"),
    url(r"^view/next_month$", view_diary_next_month, name="view-next-month"),
    # View for events by tag. This needs to come *after* the year view, to
    # avoid years being parsed as tags:
    url(r"^view/(?P<event_type>[\w-]+)/$", view_diary, name="type-view"),
    # View individual showing
    url(
        r"^showing/id/(?P<showing_id>\d+)/$",
        view_showing,
        name="single-showing-view",
    ),
    # All showings for a given event
    url(
        r"^event/id/(?P<event_id>\d+)/$", view_event, name="single-event-view"
    ),
    url(
        r"^event/(?P<event_slug>[\w\-_]*),(?P<event_id>\d+)/$",
        view_event,
        name="single-event-view-with-slug",
    ),
    # As above, for legacy event ID:
    url(
        r"^event/oldid/(?P<legacy_id>\d+)/$",
        view_event,
        name="single-event-view-legacyid",
    ),
    # Archive:
    url(r"^archive/$", ArchiveIndex.as_view(), name="archive-view-index"),
    url(
        r"^archive/(?P<year>\d{4})/$",
        ArchiveYear.as_view(),
        name="archive-view-year",
    ),
    url(
        r"^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/$",
        ArchiveMonth.as_view(),
        name="archive-view-month",
    ),
    # Search
    url(r"^archive/search/$", ArchiveSearch.as_view(), name="archive-search"),
    # RSS feed
    url(
        r"^rss/$",
        toolkit.diary.feeds.BasicWhatsOnFeed(),
        name="view-diary-rss",
    ),
]

diary_urls = [
    # Used for cancelling an edit action:
    url(
        r"^edit/cancel/?$",
        cancel_edit,
        name="cancel-edit",
    ),
    # View lists of events for editing:
    url(
        r"^edit/?$",
        edit_diary_list,
        name="default-edit",
    ),
    url(r"^edit/calendar/?$", edit_diary_calendar, name="diary-edit-calendar"),
    url(
        r"^edit/calendar/(?P<year>\d{4})/(?P<month>\d{1,2})/?$",
        edit_diary_calendar,
    ),
    url(
        r"^edit/calendar/(?P<year>\d{4})/(?P<month>\d{1,2})/"
        r"(?P<day>\d{1,2})/?$",
        edit_diary_calendar,
    ),
    url(
        r"^edit/json/$",
        edit_diary_data,
        name="edit-diary-data",
    ),
    url(
        r"^edit/(?P<year>\d{4})/?$",
        edit_diary_list,
        name="year-edit",
    ),
    url(
        r"^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/?$",
        edit_diary_list,
        name="month-edit",
    ),
    url(
        r"^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})",
        edit_diary_list,
        name="day-edit",
    ),
    # Edit an event: view event before editing
    url(
        r"^edit/event/id/(?P<event_id>\d+)/view/$",
        event_detail_view,
        name="edit-event-details-view",
    ),
    # Edit an event
    url(
        r"^edit/event/id/(?P<event_id>\d+)/$",
        EditEventView.as_view(),
        name="edit-event-details",
    ),
    # Edit a showing (includes delete / add a new showing)
    url(
        r"^edit/showing/id/(?P<showing_id>\d+)/$",
        edit_showing,
        name="edit-showing",
    ),
    # Edit rota notes for a showing
    url(
        r"^edit/showing/id/(?P<showing_id>\d+)/rota_notes/$",
        edit_showing_rota_notes,
        name="edit-showing-rota-notes",
    ),
    # Edit ideas
    url(
        r"^edit/ideas/(?P<year>\d{4})/(?P<month>\d{1,2})/$",
        edit_ideas,
        name="edit-ideas",
    ),
    # Delete a showing
    url(
        r"^edit/showing/id/(?P<showing_id>\d+)/delete$",
        delete_showing,
        name="delete-showing",
    ),
    # Add a new event + showing
    url(r"^edit/event/add$", add_event, name="add-event"),
    # Edit event types
    url(
        r"^edit/eventtemplates/",
        edit_event_templates,
        name="edit_event_templates",
    ),
    url(r"^edit/eventtags/", edit_event_tags, name="edit_event_tags"),
    # Edit event roles
    url(r"^edit/roles/", edit_roles, name="edit_roles"),
    # The slightly OTT regex in the following will match:
    # "rota" "rota/" "rota/2001/01" "rota/2001/01/" "rota/2001/1/02"
    # "rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    # View rota
    url(
        r"^(?P<field>rota|copy|terms|copy_summary)(/|/(?P<year>\d{4})/"
        r"(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$",
        view_event_field,
        name="view_event_field",
    ),
    # As above, will match:
    # "edit/rota" "edit/rota/" "edit/rota/2001/01" "edit/rota/2001/01/"
    # "edit/rota/2001/1/02" "edit/rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    url(
        r"^edit/rota(/|/(?P<year>\d{4})/"
        r"(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$$",
        EditRotaView.as_view(),
        name="rota-edit",
    ),
    url(r"^rota/vacancies$", view_rota_vacancies, name="view-rota-vacancies"),
    # Ajax calls:
    url("^edit/setprefs$", set_edit_preferences, name="set_edit_preferences"),
    url("^messages$", get_messages, name="get-messages"),
    # Printed programme archive edit/upload:
    url(
        "^printedprogrammes$",
        printed_programme_edit,
        name="edit-printed-programmes",
        kwargs={"operation": "edit"},
    ),
    url(
        "^printedprogrammes/add$",
        printed_programme_edit,
        name="add-printed-programme",
        kwargs={"operation": "add"},
    ),
    # Force a 500 error, to test error emailing
    url(r"error/$", view_force_error),
]

diary_urls += [
    url("^mailout/$", mailout, name="members-mailout"),
    url("^mailout/send$", exec_mailout, name="exec-mailout"),
    url("^mailout/send/progress$", mailout_progress, name="mailout-progress"),
    url("^mailout/test$", mailout_test_send, name="mailout-test-send"),
]
