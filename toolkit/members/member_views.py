import logging

from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Q
from django.urls import reverse
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.views.decorators.http import require_safe, require_http_methods
from django.conf import settings

from toolkit.members.forms import NewMemberForm, MemberForm
from toolkit.members.models import Member, Volunteer
from toolkit.util import compare_constant_time
from toolkit.toolkit_auth.decorators import ip_or_permission_required

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@ip_or_permission_required(
    ip_addresses=settings.CUBE_IP_ADDRESSES, permission="toolkit.write"
)
@require_http_methods(["GET", "POST"])
def add_member(request):
    # If this view is called with GET then display the form to enter a new
    # member. If called with POST then take parameters out of the body of
    # the request and create a new member
    if request.method == "POST":
        # Create new member object
        instance = Member()
        # Create form object to process the submitted data (data is pulled
        # out of the request.POST automatically)
        form = NewMemberForm(request.POST, instance=instance)
        # Validate form fields
        if form.is_valid():
            # Check for existing email address:

            if (
                instance.email
                and Member.objects.filter(email=instance.email).exists()
            ):
                logger.info(
                    f"Member with email {instance.email} already in database"
                )
                messages.add_message(
                    request,
                    messages.WARNING,
                    f"{instance.email} already in members' database",
                )
                return HttpResponseRedirect(
                    reverse(
                        "search-members",
                        query={"email": instance.email, "q": ""},
                    )
                )

            # Form is valid, save data:
            logger.info(f"Adding member '{instance.name} <{instance.email}>'")
            member = form.save(commit=False)
            member.gdpr_opt_in = timezone.now()
            member.save()
            # Member added ok, new blank form:
            form = NewMemberForm()
            messages.add_message(
                request, messages.SUCCESS, f"Added member: {instance.number}"
            )
            return HttpResponseRedirect(reverse("add-member"))
    elif request.method == "GET":
        # GET request; create form object with default values
        form = NewMemberForm()

    context = {
        "form": form,
    }
    return render(request, "form_new_member.html", context)


@permission_required("toolkit.read")
@require_safe
def search(request):
    search_terms = request.GET.get("q", None)
    email_search = request.GET.get("email", None)
    results = None

    results = Member.objects
    if email_search:
        results = results.filter(email=email_search)
    if search_terms:
        results = results.filter(
            Q(name__icontains=search_terms)
            | Q(email__icontains=search_terms)
            | Q(number=search_terms)
        ).order_by("name")
    if search_terms or email_search:
        context = {
            "search_terms": search_terms or email_search,
            "members": results,
            "membership_expiry_enabled": settings.MEMBERSHIP_EXPIRY_ENABLED,
        }
        return render(request, "search_members_results.html", context)

    context = {}
    return render(request, "search_members.html", context)


@permission_required("toolkit.read")
@require_safe
def view(request, member_id):
    # Is this view actually used?
    member = get_object_or_404(Member, id=member_id)
    return render(
        request,
        "view_member.html",
        {
            "member": member,
            "membership_expiry_enabled": settings.MEMBERSHIP_EXPIRY_ENABLED,
        },
    )


@require_http_methods(["GET", "POST"])
def delete_member(request, member_id):

    if not _check_access_permitted_for_member_key(
        "toolkit.write", request, member_id
    ):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required("toolkit.write")(delete_member)(
            request, member_id
        )
        # See comments in edit_member
        # TODO if a punter has already deleted themselves and clicks
        # on their mailout link again, they will get the login page, which
        # will probably confuse them.

    member = get_object_or_404(Member, id=member_id)

    # Did we get access to this page using a valid email key?
    access_using_key = _member_key_matches_request(request, member)

    if request.method == "GET" and not access_using_key:
        # Only allow GET requests to delete things if they were accompanied
        # by a valid access key for the given member
        return HttpResponseNotAllowed(["POST"])

    user_has_permission = request.user.has_perm("toolkit.write")

    vol = None
    try:
        vol = member.volunteer
    except Volunteer.DoesNotExist:
        pass

    # Check the person being deleted isn't an active volunteer.
    if vol and vol.active:
        # Volunteers who tried to delete their own record using an email link
        # get a special message:
        if access_using_key:
            logger.info(
                f"Futile attempt by active volunteer {member.name} <{member.email}> to delete themselves"
            )
            # TODO send mail to admins
            return render(request, "email_admin.html")
        else:
            messages.add_message(
                request,
                messages.ERROR,
                f"Can't delete active volunteer {member.name} ({member.number}). Retire them first.",
            )
            logger.info(
                f"Attempt to delete active volunteer {member.number} {member.name} <{member.email}>"
            )
            return HttpResponseRedirect(reverse("search-members"))
    # Logged in, and not following an email link, so just delete:
    elif user_has_permission and not access_using_key:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Deleted member: {member.number} ({member.name})",
        )
        logger.info(
            f"Member {member.number} {member.name} <{member.email}> deleted by admin"
        )
        member.delete()  # This will delete associated volunteer record, if any
        return HttpResponseRedirect(reverse("search-members"))
    # Not logged in (or logged in, but using a valid email link) must be an
    # email link, so confirm:
    else:
        confirmed = request.GET.get("confirmed", "no")
        if confirmed == "yes":
            logger.info(
                f"Member {member.number} {member.name} <{member.email}> self-deleted"
            )
            member.delete()
            return HttpResponseRedirect(reverse("goodbye"))
        else:
            return render(request, "confirm-deletion.html")


def _member_key_matches_request(request, member):
    """
    Utility method; returns True if the current request has a value 'k'
    which is the same as the mailout_key for the given member_object.
    """
    try:
        member_key = ""
        if request.method == "GET":
            member_key = request.GET.get("k", None)
        elif request.method == "POST":
            member_key = request.POST.get("k", None)

        assert not isinstance(member_key, bytes)
        if isinstance(member_key, str):
            # Use compare_constant_time instead of == to avoid timing
            # attacks (no, really - read up on it)
            return compare_constant_time(
                member.mailout_key.encode("ascii"), member_key.encode("ascii")
            )
            # Keys should really both be ASCII, so this is very unlikely to
            # raise an error unless someone intentionally feeds in
            # junk
    except UnicodeEncodeError:
        # If key value is garbage:
        return False


def _check_access_permitted_for_member_key(permission, request, member_id):
    """
    Utility method; returns True if either user is logged on and has the
    given permission, or if the current request has a value 'k' which is the
    same as the mailout_key for the given member_id."""
    # Check if user is logged in and has permission to edit:
    access_permitted = request.user.has_perm(permission)

    # If not, check if a 'k' parameter was supplied in the request, and if it
    # matches the member's mailout_key then go ahead
    if not access_permitted:
        try:
            member = Member.objects.get(id=member_id)
            access_permitted = _member_key_matches_request(request, member)
        except ObjectDoesNotExist:
            # If member doesn't exist, or key value is garbage:
            access_permitted = False

    return access_permitted


# This view (and unsubscribe_member below) can be accessed both by logged in
# users and if the magic key associated with the member record is passed in the
# request
@require_http_methods(["GET", "POST"])
def edit_member(request, member_id):

    if not _check_access_permitted_for_member_key(
        "toolkit.write", request, member_id
    ):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required("toolkit.write")(edit_member)(
            request, member_id
        )
        # (To elaborate:
        #    permission_required('toolkit.write')
        # is the decorator used elsewhere. Writing:
        #    permission_required('toolkit.write')(edit_member)
        # returns the function with the decorator applied, then
        #
        # permission_required('toolkit.write')(edit_member)(request, member_id)
        #
        # calls the wrapped function, passing in the arguments originaly
        # supplied. Capice?

    member = get_object_or_404(Member, id=member_id)

    user_has_permission = request.user.has_perm("toolkit.write")

    context = {}

    if request.method == "POST":
        form = MemberForm(
            request.POST,
            instance=member,
            hide_internal_fields=not user_has_permission,
        )
        if form.is_valid():
            logger.info(
                f"Saving changes to member '{member.name}' (id: {member.pk})"
            )
            form.save()
            messages.add_message(
                request, messages.SUCCESS, f"Member {member.number} updated"
            )
            if request.user.has_perm("toolkit.write"):
                return HttpResponseRedirect(reverse("search-members"))
    else:
        form = MemberForm(
            instance=member, hide_internal_fields=not user_has_permission
        )

    context = {
        "member": member,
        "form": form,
        "membership_expiry_enabled": settings.MEMBERSHIP_EXPIRY_ENABLED,
        "membership_length_days": settings.MEMBERSHIP_LENGTH_DAYS,
    }
    return render(request, "form_member.html", context)


# This view (and edit_member above) can be accessed both by logged in users and
# if the magic key associated with the member record is passed in in the
# request
@require_http_methods(["GET", "POST"])
def unsubscribe_member(request, member_id):

    if not _check_access_permitted_for_member_key(
        "toolkit.write", request, member_id
    ):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required("toolkit.write")(unsubscribe_member)(
            request, member_id
        )

    member = get_object_or_404(Member, id=member_id)

    if request.method == "POST":
        # Default to unsubscribe
        action = request.POST.get("action", "unsubscribe")
        confirm = request.POST.get("confirm", False)
        if confirm == "yes" and action in ("unsubscribe", "subscribe"):
            member.mailout = action == "subscribe"
            member.save()
            logger.info(
                f"{action} member '{member.name}' (id: {member.pk}) from mailing list"
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Member {member.number} {action}d",
            )

    action = "unsubscribe" if member.mailout else "subscribe"

    return render(
        request,
        "form_member_edit_subs.html",
        {"member": member, "action": action},
    )


# This view can be accessed both by logged in users and if the magic key
# associated with the member record is passed in in the request.  The
# difference with the above view is that this one does not ask for user
# confirmation.  The idea is that this view is called from a script to
# programmatically unsubcribe members if their emails bounce (meeting certain
# bouncing criteria - e.g. not vacation responses )


@require_http_methods(["GET"])
def unsubscribe_member_right_now(request, member_id):

    if not _check_access_permitted_for_member_key(
        "toolkit.write", request, member_id
    ):
        return permission_required("toolkit.write")(unsubscribe_member)(
            request, member_id
        )

    member = get_object_or_404(Member, id=member_id)

    action = "unsubscribe"
    member.mailout = False
    member.save()
    logger.info(
        f"{action} member '{member.name}' (id: {member.pk}) from mailing list"
    )
    messages.add_message(
        request, messages.SUCCESS, f"Member {member.number} {action}d"
    )

    return render(
        request,
        "form_member_edit_subs.html",
        {"member": member, "action": action},
    )


@require_http_methods(["GET", "POST"])
def opt_in(request, member_id):

    if not _check_access_permitted_for_member_key(
        "toolkit.write", request, member_id
    ):
        return permission_required("toolkit.write")(unsubscribe_member)(
            request, member_id
        )

    member = get_object_or_404(Member, id=member_id)

    if request.method == "POST":
        # Default to opt-in
        action = request.POST.get("action", "opt-in")
        confirm = request.POST.get("confirm", False)
        if confirm == "yes":
            if action == "opt-in":
                member.gdpr_opt_in = timezone.now()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Thank you {member.name} for opting in to continue to "
                    "receive our emails",
                )
            else:  # opt-out
                member.gdpr_opt_in = None
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "We are sorry to see you have opted out. If you do not "
                    "opt-in by 25 May 2018 we will delete your membership "
                    "from our records.",
                )
            member.save()

            logger.info(
                f"Member '{member.name}' (id: {member.pk}) <{member.email}>: {action} on {member.gdpr_opt_in}"
            )

    action = "opt-out" if member.gdpr_opt_in else "opt-in"

    return render(
        request,
        "form_member_edit_opt_in.html",
        {"member": member, "action": action},
    )


@permission_required("toolkit.read")
@require_safe
def member_statistics(request):
    # View for the 'statistics' page of the 'membership database'

    # Get 10 most popular email domains:
    email_stats = Member.objects.get_stat_popular_email_domains()
    # Get 10 most popular postcode prefixes:
    postcode_stats = Member.objects.get_stat_popular_postcode_prefixes()

    # Some of the simpler stats are done using the django ORM
    context = {
        # Results of complex queries:
        "email_stats": email_stats,
        "postcode_stats": postcode_stats,
        # Total number of members:
        "m_count": Member.objects.count(),
        # Members with an email address that isn't null/blank:
        "m_email_count": Member.objects.filter(email__isnull=False)
        .exclude(email="")
        .count(),
        # Members with an email address that isn't null/blank, where mailout
        # hasn't failed & they haven't unsubscribed:
        "m_email_viable": Member.objects.mailout_recipients().count(),
        # Members with an email address that isn't null/blank, where mailout
        # hasn't failed & they have unsubscribed:
        "m_email_unsub": Member.objects.filter(email__isnull=False)
        .exclude(email="")
        .exclude(mailout_failed=True)
        .exclude(mailout=True)
        .count(),
        # Members with a postcode that isn't null / blank
        "m_postcode": Member.objects.filter(postcode__isnull=False)
        .exclude(postcode="")
        .count(),
        # Members who aren't actually members, who don't get the mailout
        "m_cruft": Member.objects.filter(email__isnull=False)
        .exclude(email="")
        .exclude(mailout_failed=True)
        .exclude(mailout=True)
        .exclude(is_member=True)
        .count(),
        # Members with email without GDPR opt-in
        "m_no_gdpr": Member.objects.mailout_recipients()
        .filter(gdpr_opt_in__isnull=True)
        .count(),
    }
    if settings.MEMBERSHIP_EXPIRY_ENABLED:
        extra_context = {
            "m_unexpired_count": Member.objects.unexpired().count(),
            "m_expired_count": Member.objects.expired().count(),
        }
        context.update(extra_context)

    return render(request, "stats.html", context)


@permission_required("toolkit.read")
@require_safe
def member_duplicates(request):

    order = request.GET.get("order", "email")
    sort_type = "email"

    dupes = (
        Member.objects.values("email")
        .exclude(email="")
        .annotate(Count("id"))
        .filter(id__count__gt=1)
    )

    members = Member.objects.filter(
        email__in=[item["email"] for item in dupes]
    )

    if "number" in order:
        members = members.order_by("number")
        sort_type = "number"
    if "name" in order:
        members = members.order_by("name")
        sort_type = "name"
    if "email" in order:
        members = members.order_by("email")
        sort_type = "email"
    if "created-most-recent-first" in order:
        members = members.order_by("-created_at")
        sort_type = "creation date, most recent first"
    if "created-oldest-first" in order:
        members = members.order_by("created_at")
        sort_type = "creation date, oldest first"
    if "updated-most-recent-first" in order:
        members = members.order_by("-updated_at")
        sort_type = "last update, most recent first"
    if "updated-oldest-first" in order:
        members = members.order_by("updated_at")
        sort_type = "last update, oldest first"

    context = {
        "sort_type": sort_type,
        "members": members,
        "dupe_count": len(dupes),
        "member_count": len(members),
    }

    return render(request, "dupes.html", context)


@require_safe
def member_homepages(request):
    members = (
        Member.objects.filter(website__isnull=False)
        .exclude(website="")
        .order_by("number")
        .values("name", "website")
    )
    return render(request, "homepages.html", {"members": members})


def goodbye(request):
    return render(request, "goodbye.html")
