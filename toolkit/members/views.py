import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
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
    message = None
    if request.method == 'POST':
        instance = toolkit.members.models.Member()
        form = toolkit.members.forms.NewMemberForm(request.POST, instance=instance)
        if form.is_valid():
            logger.info("Adding member '%s'".format(instance.name))
            form.save()
            # Member added ok, new blank form:
            form = toolkit.members.forms.NewMemberForm()
            message = "Added member: {0}".format(instance.number)
    else:
        form = toolkit.members.forms.NewMemberForm()

    context = {
        'form' : form,
        'message' : message,
    }
    return render_to_response('form_new_member.html', RequestContext(request, context))

@require_read_auth
def search(request, volunteers=False):
    search_terms = request.GET.get('q', None)
    show_edit_link = bool(request.GET.get('show_edit_link', None))
    show_delete_link = bool(request.GET.get('show_delete_link', None))
    results = None
    print show_edit_link, show_delete_link

    if search_terms:
        results = Member.objects.filter(Q(name__icontains = search_terms) | Q(email__icontains = search_terms) | Q(number = search_terms)).order_by('name')
        context = {
                'search_terms' : search_terms,
                'members' : results,
                'show_edit_link' : show_edit_link,
                'show_delete_link' : show_delete_link,
                }
        return render_to_response('search_members_results.html', RequestContext(request, context))

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
    return render_to_response('view_member.html', RequestContext(request, context))

@require_write_auth
def delete_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        member.delete() # This will delete associated volunteer record, if any

    return HttpResponseRedirect(reverse("search-members"))

@require_write_auth
def delete_volunteer(request, member_id):
    rsp = "del_vol"
    return HttpResponse(rsp)

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
    return render_to_response('form_member.html', RequestContext(request, context))

@require_read_auth
def view_volunteer_list(request):
    volunteers = Volunteer.objects.filter(active = True).order_by('member__name').select_related()
    # Build dict of volunteer pk -> list of role names (avoid lots of queries during template render)
    roles = {}
    for vol, role in volunteers.filter(active = True).order_by('roles__name').values_list('id', 'roles__name'):
        roles.setdefault(vol, []).append(role)

    role_vol_map = {}
    for role, vol in Role.objects.filter(volunteer__active = True).values_list('name', 'volunteer__member__name').order_by('volunteer__member__name'):
        role_vol_map.setdefault(role, []).append(vol)


    context = {
            'volunteers' : volunteers,
            'roles' : roles,
            'role_vol_map' : role_vol_map,
            'default_mugshot' : settings.DEFAULT_MUGSHOT,
    }
    return render_to_response('volunteer_list.html', context)

def add_volunteer(request):
    rsp = "add_vol"
    return HttpResponse(rsp)

def select_volunteer(request, inactive=False):
    rsp = "sel_vol %s" % str(inactive)
    return HttpResponse(rsp)

def activate_volunteer(request):
    rsp = "activate_vol"
    return HttpResponse(rsp)

@require_write_auth
def edit_volunteer(request, member_id):
    rsp = "editvol"
    return HttpResponse(rsp)

@require_read_auth
def member_statistics(request):
    cursor = django.db.connection.cursor()
    cursor.execute("""SELECT SUBSTRING_INDEX(`email`, '@', -1) as domain, COUNT(1) as num  FROM Members WHERE email != '' GROUP BY domain  ORDER BY num DESC LIMIT 10""")
    email_stats = [ row for row in cursor.fetchall() ]
    cursor.close()
    cursor = django.db.connection.cursor()
    cursor.execute("""SELECT SUBSTRING_INDEX(`postcode`, ' ', 1) as firstbit, COUNT(1) as num FROM Members WHERE postcode != '' GROUP BY firstbit ORDER BY num DESC LIMIT 10""")
    postcode_stats = [ row for row in cursor.fetchall() ]
    cursor.close()

    context = {
            'email_stats' : email_stats,
            'postcode_stats' : postcode_stats,
            'm_count' : Member.objects.count(),
            'm_email_count' : Member.objects.filter(email__isnull = False).exclude(email = '').count(),
            'm_email_viable' : Member.objects.filter(email__isnull = False).exclude(email = '').exclude(mailout_failed=True).count(),
            'm_email_unsub' : Member.objects.exclude(mailout = False).count(),
            'm_postcode' : Member.objects.filter(postcode__isnull = False).exclude(postcode = '').count(),
    }


    return render_to_response('stats.html', context)
