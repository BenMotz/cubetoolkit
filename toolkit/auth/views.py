import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
import django.conf

from django import forms

import toolkit.auth.check as check

logger = logging.getLogger(__name__)

class AuthForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput)

def auth(request, atype):
    auth_types = atype.split(',')
    form = None
    context = { 'atype' : atype, }
    logger.debug("Requesting authorisation type: %s", str(atype))

    # Valid request?
    for auth_type in auth_types:
        if auth_type not in django.conf.settings.CUBE_AUTH:
            logger.error("Requested invalid authorisation type: {0}".format(auth_type))
            raise Http404('Invalid authorisation requested')

    # Already authorised for any of the requested types?
    authorised = check._has_auth_any(request, auth_types)

    # Not authorised, and credentials have been submitted:
    if request.method == 'POST' and authorised == False:
        form = AuthForm(request.POST)
        if form.is_valid():
            check._set_auth_from_credentials(request, form.cleaned_data['username'], form.cleaned_data['password'])
            authorised = check._has_auth_any(request, auth_types)
            if not authorised:
                msg = "Unrecognised username/password for %s access" % (" or ".join(auth_types),)
                logger.info(msg)
                context['message'] = msg

    if authorised:
        redirect_to = request.session.pop('next', None) or reverse("default-view")
        logger.info("Authenticated and authorised, redirecting to {0}".format(redirect_to))
        return HttpResponseRedirect(redirect_to)
    else:
        # Always use a new form:
        context['form'] = form or AuthForm()
        return render_to_response('form_auth.html', RequestContext(request, context))

def clear_auth(request):
    logger.info("Logging out")
    request.session.pop('write_auth', None)
    request.session.pop('read_auth', None)

    # Redirect in session?
    redirect_to = request.session.pop('next', None)
    if redirect_to:
        return HttpResponseRedirect(redirect_to)
    else:
        # If not, very bare confirmation:
        return HttpResponse("<html><head><title>Logged out</title></head><body><h1>Logged out</h1></body></html>")

