import logging

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST, require_safe, require_http_methods


import toolkit.members.forms
from toolkit.members.models import Member
from toolkit.util import compare_constant_time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@permission_required('toolkit.write')
@require_http_methods(["GET", "POST"])
def add_member(request):
    # If this view is called with GET then display the form to enter a new
    # member. If called with POST then take parameters out of the body of
    # the request and create a new member
    if request.method == 'POST':
        # Create new member object
        instance = toolkit.members.models.Member()
        # Create form object to process the submitted data (data is pulled
        # out of the request.POST automatically)
        form = toolkit.members.forms.NewMemberForm(request.POST, instance=instance)
        # Validate form fields
        if form.is_valid():
            # Form is valid, save data:
            logger.info(u"Adding member '{0}'".format(instance.name))
            form.save()
            # Member added ok, new blank form:
            form = toolkit.members.forms.NewMemberForm()
            messages.add_message(request, messages.SUCCESS, u"Added member: {0}".format(instance.number))
            return HttpResponseRedirect(reverse("add-member"))
    elif request.method == 'GET':
        # GET request; create form object with default values
        form = toolkit.members.forms.NewMemberForm()

    context = {
        'form': form,
    }
    return render(request, 'form_new_member.html', context)


@login_required
@require_safe
def search(request):
    search_terms = request.GET.get('q', None)
    show_edit_link = bool(request.GET.get('show_edit_link', None))
    show_delete_link = bool(request.GET.get('show_delete_link', None))
    results = None

    if search_terms:
        results = Member.objects.filter(  Q(name__icontains=search_terms)
                                        | Q(email__icontains=search_terms)
                                        | Q(number=search_terms)
                                       ).order_by('name')
        context = {
            'search_terms': search_terms,
            'members': results,
            'show_edit_link': show_edit_link,
            'show_delete_link': show_delete_link,
        }
        return render(request, 'search_members_results.html', context)

    context = {
        'show_edit_link': show_edit_link,
        'show_delete_link': show_delete_link,
    }
    return render(request, 'search_members.html', context)


@login_required
@require_safe
def view(request, member_id):
    # Is this view actually used?
    member = get_object_or_404(Member, id=member_id)
    return render(request, 'view_member.html', {'member': member})


@permission_required('toolkit.write')
@require_POST
def delete_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    logger.info(u"Deleting member '{0}'".format(member.name))
    member.delete()  # This will delete associated volunteer record, if any
    messages.add_message(request, messages.SUCCESS, u"Deleted member: {0} ({1})".format(member.number, member.name))

    return HttpResponseRedirect(reverse("search-members"))


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
            member_key = request.REQUEST.get('k', None)
            if isinstance(member_key, basestring):
                # Use compare_constant_time instead of == to avoid timing
                # attacks (no, really - read up on it)
                access_permitted = compare_constant_time(member.mailout_key.encode("ascii"), member_key.encode("ascii"))
                # Keys should really both be ASCII, so this is very unlikely to
                # raise an error unless someone intentionally feeds in
                # junk
        except (ObjectDoesNotExist, UnicodeEncodeError):
            # If member doesn't exist, or key value is garbage:
            access_permitted = False

    return access_permitted


# This view (and unsubscribe_member below) can be accessed both by logged in users and
# if the magic key associated with the member record is passed in in the request
@require_http_methods(["GET", "POST"])
def edit_member(request, member_id):

    if not _check_access_permitted_for_member_key('toolkit.write', request, member_id):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required('toolkit.write')(edit_member)(request, member_id)
        # (To elaborate:
        #    permission_required('toolkit.write')
        # is the decorator used elsewhere. Writing:
        #    permission_required('toolkit.write')(edit_member)
        # returns the function with the decorator applied, then
        #   permission_required('toolkit.write')(edit_member)(request, member_id)
        # calls the wrapped function, passing in the arguments originaly supplied.
        # Capice?

    member = get_object_or_404(Member, id=member_id)

    context = {}

    if request.method == 'POST':
        form = toolkit.members.forms.MemberForm(request.POST, instance=member)
        if form.is_valid():
            logger.info(u"Saving changes to member '{0}' (id: {1})".format(member.name, member.pk))
            form.save()
            messages.add_message(request, messages.SUCCESS, u"Member {0} updated".format(member.number))
            if request.user.has_perm('toolkit.write'):
                return HttpResponseRedirect(reverse("search-members"))
    else:
        form = toolkit.members.forms.MemberForm(instance=member)

    context = {
        'member': member,
        'form': form,
    }
    return render(request, 'form_member.html', context)


# This view (and edit_member above) can be accessed both by logged in users and
# if the magic key associated with the member record is passed in in the request
@require_http_methods(["GET", "POST"])
def unsubscribe_member(request, member_id):

    if not _check_access_permitted_for_member_key('toolkit.write', request, member_id):
        # Manually wrap this function in the standard 'permission_required'
        # decorator and call it to get the redirect to the login page:
        return permission_required('toolkit.write')(unsubscribe_member)(request, member_id)

    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        # Default to unsubscribe
        action = request.POST.get('action', 'unsubscribe')
        confirm = request.POST.get('confirm', False)
        if confirm == "yes" and action in ('unsubscribe', 'subscribe'):
            member.mailout = (action == 'subscribe')
            member.save()
            logger.info(u"{0} member '{1}' (id: {2}) from mailing list".format(action, member.name, member.pk))
            messages.add_message(request, messages.SUCCESS, u"Member {0} {1}d".format(member.number, action))

    action = 'unsubscribe' if member.mailout else 'subscribe'

    return render(request, 'form_member_edit_subs.html', {'member': member, 'action': action})


@login_required
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
        'm_email_count': Member.objects.filter(email__isnull=False)
                                       .exclude(email='')
                                       .count(),
        # Members with an email address that isn't null/blank, where mailout hasn't failed & they haven't unsubscribed:
        'm_email_viable': Member.objects.mailout_recipients().count(),
        # Members with an email address that isn't null/blank, where mailout hasn't failed & they have unsubscribed:
        'm_email_unsub': Member.objects.filter(email__isnull=False)
                                       .exclude(email='')
                                       .exclude(mailout_failed=True)
                                       .exclude(mailout=True)
                                       .count(),
        # Members with a postcode that isn't null / blank
        'm_postcode': Member.objects.filter(postcode__isnull=False)
                                    .exclude(postcode='')
                                    .count(),
    }

    return render(request, 'stats.html', context)


@require_safe
def member_homepages(request):
    members = (Member.objects.filter(website__isnull=False)
                             .exclude(website='')
                             .order_by('number')
                             .values('name', 'website'))
    return render(request, 'homepages.html', {'members': members})
