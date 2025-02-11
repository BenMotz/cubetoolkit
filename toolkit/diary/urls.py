from django.urls import re_path, path

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
    view_terms_report_csv,
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
    re_path(r"^(?:view/)?$", view_diary, name="programme-view"),
    re_path(r"^view/(?P<year>\d{4})/?$", view_diary, name="year-view"),
    re_path(
        r"^view/(?P<year>\d{4})/(?P<month>\d{1,2})/?$",
        view_diary,
        name="month-view",
    ),
    re_path(
        r"^view/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/?$",
        view_diary,
        name="day-view",
    ),
    re_path(r"^view/this_week$", view_diary_this_week, name="view-this-week"),
    re_path(r"^view/next_week$", view_diary_next_week, name="view-next-week"),
    re_path(
        r"^view/this_month$", view_diary_this_month, name="view-this-month"
    ),
    re_path(
        r"^view/next_month$", view_diary_next_month, name="view-next-month"
    ),
    # View for events by tag. This needs to come *after* the year view, to
    # avoid years being parsed as tags:
    re_path(r"^view/(?P<event_type>[\w-]+)/$", view_diary, name="type-view"),
    # View individual showing
    re_path(
        r"^showing/id/(?P<showing_id>\d+)/$",
        view_showing,
        name="single-showing-view",
    ),
    # All showings for a given event
    re_path(
        r"^event/id/(?P<event_id>\d+)/$", view_event, name="single-event-view"
    ),
    re_path(
        r"^event/(?P<event_slug>[\w\-_]*),(?P<event_id>\d+)/$",
        view_event,
        name="single-event-view-with-slug",
    ),
    # As above, for legacy event ID:
    re_path(
        r"^event/oldid/(?P<legacy_id>\d+)/$",
        view_event,
        name="single-event-view-legacyid",
    ),
    # Archive:
    re_path(r"^archive/$", ArchiveIndex.as_view(), name="archive-view-index"),
    re_path(
        r"^archive/(?P<year>\d{4})/$",
        ArchiveYear.as_view(),
        name="archive-view-year",
    ),
    re_path(
        r"^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/$",
        ArchiveMonth.as_view(),
        name="archive-view-month",
    ),
    # Search
    re_path(
        r"^archive/search/$", ArchiveSearch.as_view(), name="archive-search"
    ),
    # RSS feed
    re_path(
        r"^rss/$",
        toolkit.diary.feeds.BasicWhatsOnFeed(),
        name="view-diary-rss",
    ),
]

diary_urls = [
    # Used for cancelling an edit action:
    re_path(
        r"^edit/cancel/?$",
        cancel_edit,
        name="cancel-edit",
    ),
    # View lists of events for editing:
    re_path(
        r"^edit/?$",
        edit_diary_list,
        name="default-edit",
    ),
    re_path(
        r"^edit/calendar/?$", edit_diary_calendar, name="diary-edit-calendar"
    ),
    re_path(
        r"^edit/calendar/(?P<year>\d{4})/(?P<month>\d{1,2})/?$",
        edit_diary_calendar,
    ),
    re_path(
        r"^edit/calendar/(?P<year>\d{4})/(?P<month>\d{1,2})/"
        r"(?P<day>\d{1,2})/?$",
        edit_diary_calendar,
    ),
    re_path(
        r"^edit/json/$",
        edit_diary_data,
        name="edit-diary-data",
    ),
    re_path(
        r"^edit/(?P<year>\d{4})/?$",
        edit_diary_list,
        name="year-edit",
    ),
    re_path(
        r"^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/?$",
        edit_diary_list,
        name="month-edit",
    ),
    re_path(
        r"^edit/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})",
        edit_diary_list,
        name="day-edit",
    ),
    # Edit an event: view event before editing
    re_path(
        r"^edit/event/id/(?P<event_id>\d+)/view/$",
        event_detail_view,
        name="edit-event-details-view",
    ),
    # Edit an event
    re_path(
        r"^edit/event/id/(?P<event_id>\d+)/$",
        EditEventView.as_view(),
        name="edit-event-details",
    ),
    # Edit a showing (includes delete / add a new showing)
    re_path(
        r"^edit/showing/id/(?P<showing_id>\d+)/$",
        edit_showing,
        name="edit-showing",
    ),
    # Edit rota notes for a showing
    re_path(
        r"^edit/showing/id/(?P<showing_id>\d+)/rota_notes/$",
        edit_showing_rota_notes,
        name="edit-showing-rota-notes",
    ),
    # Edit ideas
    re_path(
        r"^edit/ideas/(?P<year>\d{4})/(?P<month>\d{1,2})/$",
        edit_ideas,
        name="edit-ideas",
    ),
    # Delete a showing
    re_path(
        r"^edit/showing/id/(?P<showing_id>\d+)/delete$",
        delete_showing,
        name="delete-showing",
    ),
    # Add a new event + showing
    re_path(r"^edit/event/add$", add_event, name="add-event"),
    # Edit event types
    re_path(
        r"^edit/eventtemplates/",
        edit_event_templates,
        name="edit_event_templates",
    ),
    re_path(r"^edit/eventtags/", edit_event_tags, name="edit_event_tags"),
    # Edit event roles
    re_path(r"^edit/roles/", edit_roles, name="edit_roles"),
    # The slightly OTT regex in the following will match:
    # "rota" "rota/" "rota/2001/01" "rota/2001/01/" "rota/2001/1/02"
    # "rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    # View rota
    re_path(
        r"^(?P<field>rota|copy|terms|copy_summary)(/|/(?P<year>\d{4})/"
        r"(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$",
        view_event_field,
        name="view_event_field",
    ),
    path(
        "terms/csv/<int:year>/<int:month>/<int:day>",
        view_terms_report_csv,
        name="view_terms_report_csv",
    ),
    # As above, will match:
    # "edit/rota" "edit/rota/" "edit/rota/2001/01" "edit/rota/2001/01/"
    # "edit/rota/2001/1/02" "edit/rota/2001/1/2/"
    # (ie needs at least year/month, not just a year)
    re_path(
        r"^edit/rota(/|/(?P<year>\d{4})/"
        r"(?P<month>\d{1,2})/?(?P<day>(?<=/)\d{0,2})?/?)?$$",
        EditRotaView.as_view(),
        name="rota-edit",
    ),
    re_path(
        r"^rota/vacancies$", view_rota_vacancies, name="view-rota-vacancies"
    ),
    # Ajax calls:
    re_path(
        "^edit/setprefs$", set_edit_preferences, name="set_edit_preferences"
    ),
    re_path("^messages$", get_messages, name="get-messages"),
    # Printed programme archive edit/upload:
    re_path(
        "^printedprogrammes$",
        printed_programme_edit,
        name="edit-printed-programmes",
        kwargs={"operation": "edit"},
    ),
    re_path(
        "^printedprogrammes/add$",
        printed_programme_edit,
        name="add-printed-programme",
        kwargs={"operation": "add"},
    ),
    # Force a 500 error, to test error emailing
    re_path(r"error/$", view_force_error),
]

diary_urls += [
    re_path("^mailout/$", mailout, name="members-mailout"),
    re_path("^mailout/send$", exec_mailout, name="exec-mailout"),
    re_path(
        "^mailout/send/progress$", mailout_progress, name="mailout-progress"
    ),
    re_path("^mailout/test$", mailout_test_send, name="mailout-test-send"),
]
