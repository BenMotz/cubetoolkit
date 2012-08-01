import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.conf import settings

from toolkit.auth.decorators import require_write_auth, require_read_or_write_auth

import toolkit.members.forms
from toolkit.members.models import Member, Volunteer
from toolkit.diary.models import Role

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@require_read_or_write_auth
def view_volunteer_list(request):
    # Get all volunteers, sorted by name:
    volunteers = Volunteer.objects.filter(active=True).order_by('member__name').select_related()

    # Build dict of volunteer pk -> list of role names
    # and dict of role names -> volunteer names
    # (avoid lots of queries during template render)
    vol_role_map = {}
    role_vol_map = {}
    # Query for active volunteers, sorted by name
    volunteer_query = (Role.objects.filter(volunteer__active=True)
                                   .values_list('name', 'volunteer__id', 'volunteer__member__name')
                                   .order_by('volunteer__member__name', 'name'))

    for role, vol_id, vol_name in volunteer_query:
        role_vol_map.setdefault(role, []).append(vol_name)
        vol_role_map.setdefault(vol_id, []).append(role)

    # Now sort role_vol_map by role name:
    role_vol_map = sorted(role_vol_map.iteritems(), key=lambda role_name_tuple: role_name_tuple[0])
    # (now got a list  of (role, (name1, name2, ...)) tuples, rather than a dict,
    # but that's fine)

    context = {
        'volunteers': volunteers,
        'vol_role_map': vol_role_map,
        'role_vol_map': role_vol_map,
        'default_mugshot': settings.DEFAULT_MUGSHOT,
    }
    return render(request, 'volunteer_list.html', context)


@require_read_or_write_auth
def select_volunteer(request, active=True):
    # This view is called to retire / unretire a volunteer. It presents a list
    # of all volunteer names and a button. If the view is called with "action=retire"
    # in the query then it shows a "retire" button linked to the# retire url, and
    # if it's called with "action=unretire" it shows  a link to the unretire url.
    #
    # The selection of volunteers (retired vs unretired) is decided by the "active"
    # parameter to this method, which is set by the url route, depending on which
    # view was used. This is probably not the simplest way to do this...
    action_urls = {
        'retire': reverse('inactivate-volunteer'),
        'unretire': reverse('activate-volunteer'),
    }

    action = request.GET.get('action', None)
    if action not in action_urls:
        logger.error("Select volunteer called with unknown action: %s", action)
        raise Http404('Invalid action')

    active = bool(active)
    volunteers = Volunteer.objects.filter(active=active).order_by('member__name').select_related()

    context = {
        'volunteers': volunteers,
        'action': action,
        'action_url': action_urls[action],
    }

    return render(request, 'select_volunteer.html', context)


@require_write_auth
def activate_volunteer(request, active=True):
    # Sets the 'active' value for the volunteer with the id passed  in the
    # 'volunteer' parameter of the POST request
    if request.method != 'POST':
        return HttpResponse("Not allowed", status=405, mimetype="text/plain")

    vol_pk = request.POST.get('volunteer', None)

    logger.info("Set volunteer.active to %s for volunteer %s", str(active), vol_pk)

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
        mem_form = toolkit.members.forms.MemberFormWithoutNotes(request.POST, prefix="mem", instance=member)
        if vol_form.is_valid() and mem_form.is_valid():
            logger.info("Saving changes to volunteer '%s' (id: %s)", volunteer.member.name, str(volunteer.pk))
            mem_form.save()
            volunteer.member = member
            vol_form.save()
            # Go to the volunteer list view:
            return HttpResponseRedirect(reverse("view-volunteer-list"))
    else:
        vol_form = toolkit.members.forms.VolunteerForm(prefix="vol", instance=volunteer)
        mem_form = toolkit.members.forms.MemberFormWithoutNotes(prefix="mem", instance=volunteer.member)

    context = {
        'pagetitle': 'Add Volunteer' if create_new else 'Edit Volunteer',
        'default_mugshot': settings.DEFAULT_MUGSHOT,
        'volunteer': volunteer,
        'vol_form': vol_form,
        'mem_form': mem_form,
    }
    return render(request, 'form_volunteer.html', context)
