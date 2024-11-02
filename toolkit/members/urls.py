from django.urls import re_path

from toolkit.members.volunteer_views import (
    view_volunteer_list,
    view_volunteer_summary,
    view_volunteer_role_report,
    edit_volunteer,
    select_volunteer,
    export_volunteers_as_csv,
    activate_volunteer,
    add_volunteer_training_record,
    add_volunteer_training_group_record,
    view_volunteer_training_records,
    delete_volunteer_training_record,
)

from toolkit.members.member_views import (
    add_member,
    search,
    view,
    edit_member,
    delete_member,
    member_statistics,
    member_duplicates,
    member_homepages,
    unsubscribe_member,
    unsubscribe_member_right_now,
    opt_in,
    goodbye,
)  # TODO rename goodbye

# Volunteers:
volunteer_urls = [
    re_path(r"^$", view_volunteer_list),
    re_path(
        r"^add/$",
        edit_volunteer,
        name="add-volunteer",
        kwargs={"volunteer_id": None, "create_new": True},
    ),
    re_path(
        r"^add-training/(?P<volunteer_id>\d+)/$",
        add_volunteer_training_record,
        name="add-volunteer-training-record",
    ),
    re_path(
        r"^delete-training/(?P<training_record_id>\d+)/$",
        delete_volunteer_training_record,
        name="delete-volunteer-training-record",
    ),
    re_path(
        r"^add-training-group/$",
        add_volunteer_training_group_record,
        name="add-volunteer-training-group-record",
    ),
    re_path(r"^view/$", view_volunteer_list, name="view-volunteer-list"),
    re_path(
        r"^view/summary/$",
        view_volunteer_summary,
        name="view-volunteer-summary",
    ),
    re_path(
        r"^view/rolereport/$",
        view_volunteer_role_report,
        name="view-volunteer-role-report",
    ),
    re_path(
        r"^view/trainingreport/$",
        view_volunteer_training_records,
        name="view-volunteer-training-report",
    ),
    re_path(
        r"^view/export/$",
        export_volunteers_as_csv,
        name="view-volunteer-export",
    ),
    re_path(
        r"^retire/select$",
        select_volunteer,
        name="retire-select-volunteer",
        kwargs={"action": "retire"},
    ),
    re_path(
        r"^unretire/select$",
        select_volunteer,
        name="unretire-select-volunteer",
        kwargs={"action": "unretire", "active": False},
    ),
    re_path(
        r"^(?P<volunteer_id>\d+)/edit$", edit_volunteer, name="edit-volunteer"
    ),
    re_path(r"^unretire$", activate_volunteer, name="activate-volunteer"),
    re_path(
        r"^retire$",
        activate_volunteer,
        name="inactivate-volunteer",
        kwargs={"set_active": False},
    ),
]

# Members:
member_urls = [
    # Internal:
    re_path(r"^add/$", add_member, name="add-member"),
    re_path(r"^search/$", search, name="search-members"),
    re_path(r"^(?P<member_id>\d+)$", view, name="view-member"),
    re_path(r"^(?P<member_id>\d+)/edit/$", edit_member, name="edit-member"),
    re_path(
        r"^(?P<member_id>\d+)/delete/$", delete_member, name="delete-member"
    ),
    re_path(r"^statistics/$", member_statistics, name="member-statistics"),
    re_path(r"^duplicates/$", member_duplicates, name="member-duplicates"),
    # External:
    re_path(r"^homepages/$", member_homepages, name="member-homepages"),
    # Semi-external (see member_views.py for details)
    re_path(
        r"^(?P<member_id>\d+)/unsubscribe/$",
        unsubscribe_member,
        name="unsubscribe-member",
    ),
    re_path(
        r"^(?P<member_id>\d+)/unsubscribe-now/$",
        unsubscribe_member_right_now,
        name="unsubscribe-member-right-now",
    ),
    re_path(r"^(?P<member_id>\d+)/opt-in/$", opt_in, name="opt_in"),
    re_path(r"^goodbye/$", goodbye, name="goodbye"),
]
