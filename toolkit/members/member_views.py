import logging

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Q
from django.urls import reverse
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.views.decorators.http import (require_POST, require_safe,
                                          require_http_methods)
from django.conf import settings
import six

from toolkit.members.forms import NewMemberForm, MemberForm
from toolkit.members.models import Member, Volunteer
from toolkit.util import compare_constant_time
from toolkit.toolkit_auth.decorators import ip_or_permission_required

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@ip_or_permission_required(ip_addresses=settings.CUBE_IP_ADDRESSES,
                           permission='toolkit.write')
@require_http_methods(["GET", "POST"])
def add_member(request):
    # If this view is called with GET then display the form to enter a new
    # member. If called with POST then take parameters out of the body of
    # the request and create a new member
    if request.method == 'POST':
        # Create new member object
        instance = Member()
        # Create form object to process the submitted data (data is pulled
        # out of the request.POST automatically)
        form = NewMemberForm(request.POST, instance=instance)
        # Validate form fields
        if form.is_valid():

            results = (Member.objects.filter(email__icontains=instance.email)
                                     .order_by('name'))
            if results:
                for result in results:
                    logger.info('Member with id %s %s <%s> already in database' %
                                (result.id, result.name, result.email))
                context = {
                    'search_terms': instance.email,
                    'members': results,
                    'membership_expiry_enabled': settings.MEMBERSHIP_EXPIRY_ENABLED,
                }
                messages.add_message(request,
                                     messages.WARNING,
                                     u"%s already in members' database" %
                                     instance.email)
                return render(request, 'search_members_results.html', context)

            # Form is valid, save data:
            logger.info(u"Adding member '{0} <{1}>'".format(
                instance.name,
                instance.email)
            )
            member = form.save(commit=False)
            member.gdpr_opt_in = timezone.now()
            member.save()
            # Member added ok, new blank form:
            form = NewMemberForm()
            messages.add_message(request, messages.SUCCESS,
                                 u"Added member: {0}".format(instance.number))
            return HttpResponseRedirect(reverse("add-member"))
    elif request.method == 'GET':
        # GET request; create form object with default values
        form = NewMemberForm()

    context = {
        'form': form,
    }
    return render(request, 'form_new_member.html', context)


@permission_required('toolkit.read')
@require_safe
def search(request):
    search_terms = request.GET.get('q', None)
    results = None

    if search_terms:
        results = Member.objects.filter(
            Q(name__icontains=search_terms) |
            Q(email__icontains=search_terms) |
            Q(number=search_terms)).order_by('name')
        context = {
            'search_terms': search_terms,
            'members': results,
            'membership_expiry_enabled': settings.MEMBERSHIP_EXPIRY_ENABLED,
        }
        return render(request, 'search_members_results.html', context)

    context = {}
    return render(request, 'search_members.html', context)


@permission_required('toolkit.read')
@require_safe
def view(request, member_id):
    # Is this view actually used?
    member = get_object_or_404(Member, id=member_id)
    return render(request, 'view_member.html', {
        'member': member,
        'membership_expiry_enabled': settings.MEMBERSHIP_EXPIRY_ENABLED,
    })


@require_http_methods(["GET", "POST"])
def delete_member(request, member_id):

    if not _check_access_permitted_for_member_key(
            'toolkit.write', request, member_id):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required('toolkit.write')(edit_member)(
            request, member_id)
        # See comments in edit_member
        # TODO if a punter has already deleted themselves and clicks
        # on their mailout link again, they will get the login page, which
        # will probablu confuse them.

    member = get_object_or_404(Member, id=member_id)

    user_has_permission = request.user.has_perm('toolkit.write')

    if request.user.has_perm('toolkit.write'):

        # Check the person being deleted isn't an active volunteer.
        # This is mostly to prevent toolkit admins accidentally
        # deleting themselves by clicking on the delete link in their email
        # whilst logged on.
        vol = Volunteer.objects.filter(member__id=member_id)
        vol = vol.first()
        if vol and vol.active:
            messages.add_message(request, messages.ERROR,
                                 u"Can't delete active volunteer {0} ({1}). Retire them first.".format(
                                     member.name, member.number))
            logger.info(u"Attempt to delete active volunteer {0} {1} <{1}>".format(
                  member.number,
                  member.name,
                  member.email)
                  )

        else:
            messages.add_message(request, messages.SUCCESS,
                                 u"Deleted member: {0} ({1})".format(
                                     member.number, member.name))
            logger.info(u"Member {0} {1} <{2}> deleted by admin".format(
                  member.number,
                  member.name,
                  member.email)
                  )
            member.delete()  # This will delete associated volunteer record, if any

        return HttpResponseRedirect(reverse("search-members"))

    else:

        # Check the punter isn't an active volunteer
        vol = Volunteer.objects.filter(member__email=member.email)
        # Rashly take the first result
        vol = vol.first()
        if vol and vol.active:
            # TODO send mail to admins
            logger.info(u"Futile attempt by active volunteer {0} <{1}> to delete themselves".format(
                  vol.member.name,
                  vol.member.email)
            )
            return render(request, 'email_admin.html')

        # This is a punter deleting their own membership record
        confirmed = request.GET.get('confirmed', 'no')

        if confirmed == 'yes':

            logger.info(u"Member {0} {1} <{2}> self-deleted".format(
                  member.number,
                  member.name,
                  member.email)
                  )
            member.delete()

            return HttpResponseRedirect(reverse("goodbye"))
        else:
            return render(request, 'confirm-deletion.html')


def _check_access_permitted_for_member_key(permission, request, member_id):
    """Utility method; returns True if either user is logged on and has the
    given permission, or if the current request has a value 'k' which is the
    same as the mailout_key for the given member_id."""
    # Check if user is logged in and has permission to edit:
    access_permitted = request.user.has_perm(permission)

    # If not, check if a 'k' parameter was supplied in the request, and if it
    # matches the member's mailout_key then go ahead
    if not access_permitted:
        try:
            member = Member.objects.get(id=member_id)
            member_key = ''
            if request.method == 'GET':
                member_key = request.GET.get('k', None)
            elif request.method == 'POST':
                member_key = request.POST.get('k', None)

            assert not isinstance(member_key, six.binary_type)
            if isinstance(member_key, six.text_type):
                # Use compare_constant_time instead of == to avoid timing
                # attacks (no, really - read up on it)
                access_permitted = compare_constant_time(
                    member.mailout_key.encode("ascii"),
                    member_key.encode("ascii"))
                # Keys should really both be ASCII, so this is very unlikely to
                # raise an error unless someone intentionally feeds in
                # junk
        except (ObjectDoesNotExist, UnicodeEncodeError):
            # If member doesn't exist, or key value is garbage:
            access_permitted = False

    return access_permitted


# This view (and unsubscribe_member below) can be accessed both by logged in
# users and if the magic key associated with the member record is passed in the
# request
@require_http_methods(["GET", "POST"])
def edit_member(request, member_id):

    if not _check_access_permitted_for_member_key(
            'toolkit.write', request, member_id):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required('toolkit.write')(edit_member)(
            request, member_id)
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

    user_has_permission = request.user.has_perm('toolkit.write')

    context = {}

    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member,
                          hide_internal_fields=not user_has_permission)
        if form.is_valid():
            logger.info(u"Saving changes to member '{0}' (id: {1})".format(
                member.name, member.pk))
            form.save()
            messages.add_message(request, messages.SUCCESS,
                                 u"Member {0} updated".format(member.number))
            if request.user.has_perm('toolkit.write'):
                return HttpResponseRedirect(reverse("search-members"))
    else:
        form = MemberForm(instance=member,
                          hide_internal_fields=not user_has_permission)

    context = {
        'member': member,
        'form': form,
        'membership_expiry_enabled': settings.MEMBERSHIP_EXPIRY_ENABLED,
        'membership_length_days': settings.MEMBERSHIP_LENGTH_DAYS,
    }
    return render(request, 'form_member.html', context)


# This view (and edit_member above) can be accessed both by logged in users and
# if the magic key associated with the member record is passed in in the
# request
@require_http_methods(["GET", "POST"])
def unsubscribe_member(request, member_id):

    if not _check_access_permitted_for_member_key('toolkit.write', request,
                                                  member_id):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required('toolkit.write')(unsubscribe_member)(
            request, member_id)

    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        # Default to unsubscribe
        action = request.POST.get('action', 'unsubscribe')
        confirm = request.POST.get('confirm', False)
        if confirm == "yes" and action in ('unsubscribe', 'subscribe'):
            member.mailout = (action == 'subscribe')
            member.save()
            logger.info(u"{0} member '{1}' (id: {2}) from mailing list"
                        .format(action, member.name, member.pk))
            messages.add_message(request, messages.SUCCESS,
                                 u"Member {0} {1}d".format(
                                     member.number, action))

    action = 'unsubscribe' if member.mailout else 'subscribe'

    return render(request, 'form_member_edit_subs.html',
                  {'member': member, 'action': action})

# This view can be accessed both by logged in users and if the magic key
# associated with the member record is passed in in the request.  The
# difference with the above view is that this one does not ask for user
# confirmation.  The idea is that this view is called from a script to
# programmatically unsubcribe members if their emails bounce (meeting certain
# bouncing criteria - e.g. not vacation responses )


@require_http_methods(["GET"])
def unsubscribe_member_right_now(request, member_id):

    if not _check_access_permitted_for_member_key('toolkit.write', request,
                                                  member_id):
        return permission_required('toolkit.write')(unsubscribe_member)(
            request, member_id)

    member = get_object_or_404(Member, id=member_id)

    action = 'unsubscribe'
    member.mailout = False
    member.save()
    logger.info(u"{0} member '{1}' (id: {2}) from mailing list"
                .format(action, member.name, member.pk))
    messages.add_message(request, messages.SUCCESS,
                         u"Member {0} {1}d".format(member.number, action))

    return render(request, 'form_member_edit_subs.html',
                  {'member': member, 'action': action})


@require_http_methods(["GET", "POST"])
def opt_in(request, member_id):

    if not _check_access_permitted_for_member_key('toolkit.write', request,
                                                  member_id):
        return permission_required('toolkit.write')(unsubscribe_member)(
            request, member_id)

    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        # Default to opt-in
        action = request.POST.get('action', 'opt-in')
        confirm = request.POST.get('confirm', False)
        if confirm == "yes":
            if action == 'opt-in':
                member.gdpr_opt_in = timezone.now()
                messages.add_message(request,
                                     messages.SUCCESS,
                                     u"Thank you {0} for opting in to continue to receive our emails"
                                     .format(member.name)
                                     )
            else:   # opt-out
                member.gdpr_opt_in = None
                messages.add_message(request,
                                     messages.SUCCESS,
                                     (u"We are sorry to see you have opted out. "
                                      u"If you do not opt-in by 25 May 2018 "
                                      u"we will delete your membership from our records.")
                                     )
            member.save()

            logger.info(u"Member '{0}' (id: {1}) <{2}>: {3} on {4}"
                        .format(member.name,
                                member.pk,
                                member.email,
                                action,
                                member.gdpr_opt_in)
                        )

    action = 'opt-out' if member.gdpr_opt_in else 'opt-in'

    return render(request, 'form_member_edit_opt_in.html',
                  {'member': member, 'action': action})


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
        'email_stats': email_stats,
        'postcode_stats': postcode_stats,
        # Total number of members:
        'm_count': Member.objects.count(),
        # Members with an email address that isn't null/blank:
        'm_email_count': Member.objects
                               .filter(email__isnull=False)
                               .exclude(email='')
                               .count(),
        # Members with an email address that isn't null/blank, where mailout
        # hasn't failed & they haven't unsubscribed:
        'm_email_viable': Member.objects.mailout_recipients().count(),
        # Members with an email address that isn't null/blank, where mailout
        # hasn't failed & they have unsubscribed:
        'm_email_unsub': Member.objects
                               .filter(email__isnull=False)
                               .exclude(email='')
                               .exclude(mailout_failed=True)
                               .exclude(mailout=True)
                               .count(),
        # Members with a postcode that isn't null / blank
        'm_postcode': Member.objects
                            .filter(postcode__isnull=False)
                            .exclude(postcode='')
                            .count(),
        # Members who aren't actually members, who don't get the mailout
        'm_cruft': Member.objects
                         .filter(email__isnull=False)
                         .exclude(email='')
                         .exclude(mailout_failed=True)
                         .exclude(mailout=True)
                         .exclude(is_member=True)
                         .count(),

        # Members with email without GDPR opt-in
        'm_no_gdpr': Member.objects
                           .mailout_recipients()
                           .filter(gdpr_opt_in__isnull=True)
                           .count(),
    }
    if settings.MEMBERSHIP_EXPIRY_ENABLED:
        extra_context = {
                'm_unexpired_count': Member.objects.unexpired().count(),
                'm_expired_count': Member.objects.expired().count(),

        }
        context.update(extra_context)

    return render(request, 'stats.html', context)


@permission_required('toolkit.read')
@require_safe
def member_duplicates(request):

    order = request.GET.get('order', 'email')
    sort_type = 'email'

    dupes = (Member.objects.values('email')
                           .exclude(email='')
                           .annotate(Count('id'))
                           .filter(id__count__gt=1))

    members = Member.objects.filter(email__in=[item['email'] for item in dupes])

    if 'number' in order:
        members = members.order_by('number')
        sort_type = 'number'
    if 'name' in order:
        members = members.order_by('name')
        sort_type = 'name'
    if 'email' in order:
        members = members.order_by('email')
        sort_type = 'email'
    if 'created-most-recent-first' in order:
        members = members.order_by('-created_at')
        sort_type = 'creation date, most recent first'
    if 'created-oldest-first' in order:
        members = members.order_by('created_at')
        sort_type = 'creation date, oldest first'
    if 'updated-most-recent-first' in order:
        members = members.order_by('-updated_at')
        sort_type = 'last update, most recent first'
    if 'updated-oldest-first' in order:
        members = members.order_by('updated_at')
        sort_type = 'last update, oldest first'

    context = {
        'sort_type': sort_type,
        'members': members,
        'dupe_count': len(dupes),
        'member_count': len(members),
    }

    return render(request, 'dupes.html', context)


@require_safe
def member_homepages(request):
    members = (Member.objects.filter(website__isnull=False)
                             .exclude(website='')
                             .order_by('number')
                             .values('name', 'website'))
    return render(request, 'homepages.html', {
            'members': members}
    )


def goodbye(request):
    return render(request, 'goodbye.html')
