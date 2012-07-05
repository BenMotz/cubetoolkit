import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.db.models import Q
import django.db # Used for raw query for stats
from django.core.urlresolvers import reverse

from toolkit.auth.decorators import require_read_auth, require_write_auth

import toolkit.members.forms
from toolkit.members.models import Member

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def add_member(request):
    # If this view is called with GET then display the form to enter a new
    # member. If called with POST then take parameters out of the body of 
    # the request and create a new member
    message = None
    if request.method == 'POST':
        # Create new member object
        instance = toolkit.members.models.Member()
        # Create form object to process the submitted data (data is pulled
        # out of the request.POST automatically)
        form = toolkit.members.forms.NewMemberForm(request.POST, instance=instance)
        # Validate form fields
        if form.is_valid():
            # Form is valid, save data:
            logger.info("Adding member '%s'".format(instance.name))
            form.save()
            # Member added ok, new blank form:
            form = toolkit.members.forms.NewMemberForm()
            message = "Added member: {0}".format(instance.number)
    else:
        # GET request; create form object with default values
        form = toolkit.members.forms.NewMemberForm()

    context = {
        'form' : form,
        'message' : message,
    }
    return render(request, 'form_new_member.html', context)

@require_read_auth
def search(request):
    search_terms = request.GET.get('q', None)
    show_edit_link = bool(request.GET.get('show_edit_link', None))
    show_delete_link = bool(request.GET.get('show_delete_link', None))
    results = None
    print show_edit_link, show_delete_link

    if search_terms:
        results = Member.objects.filter(  Q(name__icontains = search_terms)
                                        | Q(email__icontains = search_terms)
                                        | Q(number = search_terms)
                                       ).order_by('name')
        context = {
                'search_terms' : search_terms,
                'members' : results,
                'show_edit_link' : show_edit_link,
                'show_delete_link' : show_delete_link,
                }
        return render(request, 'search_members_results.html', context)

    context = {
            'show_edit_link' : show_edit_link,
            'show_delete_link' : show_delete_link,
            }
    return render_to_response('search_members.html', context)


@require_read_auth
def view(request, member_id):
    # Is this view actually used?
    member = get_object_or_404(Member, id=member_id)
    return render(request, 'view_member.html', { 'member' : member })

@require_write_auth
def delete_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        member.delete() # This will delete associated volunteer record, if any

    return HttpResponseRedirect(reverse("search-members"))

@require_write_auth
def edit_member(request, member_id):
    context = {}
    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        form = toolkit.members.forms.MemberForm(request.POST, instance=member)
        if form.is_valid():
            logger.info("Saving changes to member id '%s' (id: %d)", member.name, member.pk)
            form.save()
            return HttpResponseRedirect(reverse("search-members"))
    else:
        form = toolkit.members.forms.MemberForm(instance=member)


    context = {
            'member' : member,
            'form' : form,
            }
    return render(request, 'form_member.html', context)

@require_read_auth
def member_statistics(request):
    # View for the 'statistics' page of the 'membership database'

    # A few hard-coded SQL queries to get some of the more complex numbers
    cursor = django.db.connection.cursor()
    # Get 10 most popular email domains:
    cursor.execute("SELECT "
                      "SUBSTRING_INDEX(`email`, '@', -1) AS domain, "
                      "COUNT(1) AS num "
                   "FROM Members "
                   "WHERE email != '' "
                   "GROUP BY domain "
                   "ORDER BY num DESC "
                   "LIMIT 10")
    email_stats = [ row for row in cursor.fetchall() ]
    cursor.close()
    cursor = django.db.connection.cursor()
    # Get 10 most popular postcode prefixes:
    cursor.execute("SELECT "
                        "SUBSTRING_INDEX(`postcode`, ' ', 1) AS firstbit, "
                        "COUNT(1) AS num "
                   "FROM Members "
                   "WHERE postcode != '' "
                   "GROUP BY firstbit "
                   "ORDER BY num DESC "
                   "LIMIT 10")
    postcode_stats = [ row for row in cursor.fetchall() ]
    cursor.close()

    # Some of the simpler stats are done using the django ORM
    context = {
            # Results of complex queries:
            'email_stats' : email_stats,
            'postcode_stats' : postcode_stats,
            # Total number of members:
            'm_count' : Member.objects.count(),
            # Members with an email address that isn't null/blank:
            'm_email_count' : Member.objects.filter(email__isnull=False)
                                            .exclude(email = '')
                                            .count(),
            # Members with an email address that isn't null/blank, where mailout hasn't failed and they haven't unsubscribed:
            'm_email_viable' : Member.objects.filter(email__isnull=False)
                                              .exclude(email = '')
                                              .exclude(mailout_failed=True)
                                              .filter(mailout=True)
                                              .count(),
            # Members with an email address that isn't null/blank, where mailout hasn't failed and they have unsubscribed:
            'm_email_unsub' : Member.objects.filter(email__isnull=False)
                                            .exclude(email = '')
                                            .exclude(mailout_failed=True)
                                            .exclude(mailout=True)
                                            .count(),
            # Members with a postcode that isn't null / blank
            'm_postcode' : Member.objects.filter(postcode__isnull = False)
                                         .exclude(postcode = '')
                                         .count(),
    }


    return render_to_response('stats.html', context)

def member_homepages(request):
    members = (Member.objects.filter(website__isnull = False)
                            .exclude(website = '')
                            .order_by('number')
                            .values('name', 'website'))
    return render_to_response('homepages.html', { 'members' : members })

