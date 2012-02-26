import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms.models import modelformset_factory
import django.db


from toolkit.auth.decorators import require_read_auth, require_write_auth

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    rsp = "view {0}".format(volunteers)
    return HttpResponse(rsp)

@require_write_auth
def edit_member(request, member_id):
    rsp = "edit"
    return HttpResponse(rsp)

@require_write_auth
def edit_volunteer(request, member_id):
    rsp = "editvol"
    return HttpResponse(rsp)
