import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms.models import modelformset_factory
import django.db

from toolkit.auth.decorators import require_read_auth, require_write_auth

import toolkit.members.forms
from toolkit.members.models import Member

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
            message = "Added member: {0}".format(instance.pk)
    else:
        form = toolkit.members.forms.NewMemberForm()

    context = {
        'form' : form,
        'message' : message,
    }
    return render_to_response('form_new_member.html', RequestContext(request, context))

def add_volunteer(request):
    rsp = "add_vol"
    return HttpResponse(rsp)

@require_read_auth
def search(request, volunteers=False):
    rsp = "search {0}".format(volunteers)
    return HttpResponse(rsp)

@require_read_auth
def view_list(request, volunteers=False):
    rsp = "viewlist {0}".format(volunteers)
    return HttpResponse(rsp)

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
    return render_to_response('view_member.html', context)

@require_write_auth
def edit_member(request, member_id):
    context = {}
    member = get_object_or_404(Member, id=member_id)

    context = {
            'member' : member,
            }
    return render_to_response('view_member.html', context)

@require_write_auth
def edit_volunteer(request, member_id):
    rsp = "editvol"
    return HttpResponse(rsp)

@require_read_auth
def member_statistics(request):
    rsp = "stats"
    return HttpResponse(rsp)
