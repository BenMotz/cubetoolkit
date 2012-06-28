import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.db.models import Q
import django.db # Used for raw query for stats
from django.core.urlresolvers import reverse
from django.conf import settings
# import django.db

from toolkit.auth.decorators import require_read_auth, require_write_auth

import toolkit.members.forms
from toolkit.members.models import Member, Volunteer
from toolkit.diary.models import Role

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
def search(request, volunteers=False):
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
def view(request, member_id, volunteers=False):
    context = {}
    member = get_object_or_404(Member, id=member_id)
    if volunteers and member.volunteer is None:
        raise Http404("Volunteer not found")

    context = {
            'show_volunteer' : volunteers,
            'member' : member,
            }
    return render(request, 'view_member.html', context)

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
def view_volunteer_list(request):
    # Get all volunteers, sorted by name:
    volunteers = Volunteer.objects.filter(active = True).order_by('member__name').select_related()

    # Build dict of volunteer pk -> list of role names
    # and dict of role names -> volunteer names
    # (avoid lots of queries during template render)
    vol_role_map = {}
    role_vol_map = {}
    # Query for active volunteers, sorted by name
    volunteer_query = (Role.objects.filter(volunteer__active = True)
                                   .values_list('name', 'volunteer__id', 'volunteer__member__name')
                                   .order_by('volunteer__member__name', 'name'))

    for role, vol_id, vol_name in volunteer_query:
        role_vol_map.setdefault(role, []).append(vol_name)
        vol_role_map.setdefault(vol_id, []).append(role)

    # Now sort role_vol_map by role name:
    role_vol_map = sorted(role_vol_map.iteritems(), lambda a,b: cmp(a[0], b[0]))
    # (now got a list  of (role, (name1, name2, ...)) tuples, rather than a dict,
    # but that's fine)

    context = {
            'volunteers' : volunteers,
            'vol_role_map' : vol_role_map,
            'role_vol_map' : role_vol_map,
            'default_mugshot' : settings.DEFAULT_MUGSHOT,
    }
    return render_to_response('volunteer_list.html', context)

def select_volunteer(request, active=True):
    # This view is called to retire / unretire a volunteer. It presents a list
    # of all volunteer names and a button. If the view is called with "action=retire"
    # in the query then it shows a "retire" button linked to the# retire url, and 
    # if it's called with "action=unretire" it shows  a link to the unretire url.
    #
    # The selection of volunteers (retired vs unretired) is decided by the "active"
    # parameter to this method, which is set by the url route, depending on which
    # view was used. This is probably not the simplest way to do this...
    action_urls = { 'retire' : reverse('inactivate-volunteer'),
                    'unretire' : reverse('activate-volunteer'),
                  }

    action = request.GET.get('action', None)
    if action not in action_urls:
        logging.error("Select volunteer called with unknown action: %s", action)
        raise Http404('Invalid action')

    active = bool(active)
    volunteers = Volunteer.objects.filter(active = active).order_by('member__name').select_related()

    context = {
            'volunteers' : volunteers,
            'action' : action,
            'action_url' : action_urls[action],
            }

    return render(request, 'select_volunteer.html', context)

def activate_volunteer(request, active=True):
    # Sets the 'active' value for the volunteer with the id passed  in the
    # 'volunteer' parameter of the POST request
    if request.method != 'POST':
        return HttpResponse("Not allowed", status=405, mimetype="text/plain")

    vol_pk = request.POST.get('volunteer', None)

    logging.info("Set volunteer.active to %s for volunteer %s", str(active), vol_pk)

    vol = get_object_or_404(Volunteer, id=vol_pk)

    assert type(active) is bool
    vol.active = active
    vol.save()

    return HttpResponseRedirect(reverse("view-volunteer-list"))

@require_write_auth
def edit_volunteer(request, member_id, create_new=False):
    # If called from the "add" url, then create_new will be True. If called from
    # the edit url then it'll be False

    # Depending on which way this method was called, either create a totally
    # new volunteer object with default values (add) or load the volunteer
    # object with the given member_id from the database:
    if not create_new:
        # Called from "edit" url
        volunteer = get_object_or_404(Volunteer, id=member_id)
        member = volunteer.member
    else:
        # Called from "add" url
        volunteer = Volunteer()
        member = Member()
        volunteer.member = Member()

    # Now, if the view was loaded with "GET" then display the edit form, and
    # if it was called with POST then read the updated volunteer data from the
    # form data and update and save the volunteer object:
    if request.method == 'POST':
        vol_form = toolkit.members.forms.VolunteerForm(request.POST, request.FILES, prefix="vol", instance=volunteer)
        mem_form = toolkit.members.forms.MemberForm(request.POST, prefix="mem", instance=member)
        if vol_form.is_valid() and mem_form.is_valid():
            logger.info("Saving changes to volunteer '%s' (id: %s)", volunteer.member.name, str(volunteer.pk))
            mem_form.save()
            volunteer.member = member
            # Call form save with commit=False so that it returns the vol object,
            updated_volunteer = vol_form.save(commit=False)
            # Form doesn't automatically handle role mapping, so do it manually. First get
            # list of volunteer roles from post:
            roles_from_form = set( int(role, 10) for role in request.POST.getlist('vol-roles') )
            # Now get list of roles volunteer already has:
            existing_roles = set( r[0] for r in updated_volunteer.roles.all().values_list('id') )
            # Ensure all roles listed on form are added
            updated_volunteer.roles.add(*roles_from_form)
            # Any roles in existing_roles but not in list from form should be removed:
            roles_to_remove = existing_roles.difference(roles_from_form)
            updated_volunteer.roles.remove(*roles_to_remove)

            # Now save updated volunteer object, and set update_portrait_thumbnail
            # parameter can be passed.
            # (So, to be clear, the first "save" is on the form object, and that
            # doesn't write to the database, but returns a volunteer object, and
            # then "save" is called on the volunteer object, which does write to
            # the db)
            updated_volunteer.save(update_portrait_thumbnail=True)
            #return render(request, 'form_volunteer.html', {})
            # Go to the volunteer list view:
            return HttpResponseRedirect(reverse("view-volunteer-list"))
    else:
        vol_form = toolkit.members.forms.VolunteerForm(prefix="vol", instance=volunteer)
        mem_form = toolkit.members.forms.MemberForm(prefix="mem", instance=volunteer.member)


    context = {
            'pagetitle' : 'Add Volunteer' if create_new else 'Edit Volunteer',
            'volunteer' : volunteer,
            'vol_form' : vol_form,
            'mem_form' : mem_form,
            }
    return render(request, 'form_volunteer.html', context)

@require_read_auth
def member_statistics(request):
    # View for the 'statistics' page of the 'membership database'

    # A few hard-coded SQL queries to get some of the more complex numbers
    cursor = django.db.connection.cursor()
    # Get 10 most popular email domains:
    cursor.execute("""SELECT SUBSTRING_INDEX(`email`, '@', -1) AS domain, COUNT(1) AS num FROM Members WHERE email != '' GROUP BY domain ORDER BY num DESC LIMIT 10""")
    email_stats = [ row for row in cursor.fetchall() ]
    cursor.close()
    cursor = django.db.connection.cursor()
    # Get 10 most popular postcode prefixes:
    cursor.execute("""SELECT SUBSTRING_INDEX(`postcode`, ' ', 1) AS firstbit, COUNT(1) AS num FROM Members WHERE postcode != '' GROUP BY firstbit ORDER BY num DESC LIMIT 10""")
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
            'm_email_count' : Member.objects.filter(email__isnull=False).exclude(email = '').count(),
            # Members with an email address that isn't null/blank, where mailout hasn't failed and they haven't unsubscribed:
            'm_email_viable' : Member.objects.filter(email__isnull=False).exclude(email = '').exclude(mailout_failed=True).filter(mailout=True).count(),
            # Members with an email address that isn't null/blank, where mailout hasn't failed and they have unsubscribed:
            'm_email_unsub' : Member.objects.filter(email__isnull=False).exclude(email = '').exclude(mailout_failed=True).exclude(mailout=True).count(),
            # Members with a postcode that isn't null / blank
            'm_postcode' : Member.objects.filter(postcode__isnull = False).exclude(postcode = '').count(),
    }


    return render_to_response('stats.html', context)

def member_homepages(request):
    members = Member.objects.filter(website__isnull = False).exclude(website = '').order_by('number').values('name', 'website')
    return render_to_response('homepages.html', { 'members' : members })
