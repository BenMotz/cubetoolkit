import logging

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
import django.conf

from django import forms

import toolkit.auth.check as check

class AuthForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput)

def auth(request, atype):
    auth_types = atype.split(',')
    form = None
    context = { 'atype' : atype, }
    logging.info("Auth: %s", str(atype))

    # Valid request?
    for auth_type in auth_types:
        if auth_type not in django.conf.settings.CUBE_AUTH:
            raise Http404('Invalid auth requested')

    # Already authorised?
    auth = check._has_auth_any(request, auth_types)
    if auth:
        print "alread authorised"

    # Not authorised, and credentials have been submitted:
    if request.method == 'POST' and auth == False:
        form = AuthForm(request.POST)
        if form.is_valid():
            check._set_auth_from_credentials(request, form.cleaned_data['username'], form.cleaned_data['password'])
            auth = check._has_auth_any(request, auth_types)
            if not auth:
                context['message'] = "Unrecognised username/password for %s access" % (" or ".join(auth_types),)

    if auth:
        next = request.session.pop('next', None) or reverse("default-view")
        print "Redirecting to '%s'" % (next,)
        return HttpResponseRedirect(next)
    else:
        # Always use a new form:
        context['form'] = form or AuthForm()
        return render_to_response('form_auth.html', RequestContext(request, context))

    # Store the original destination, before redirecting to the auth
    return HttpResponse("Auth: %s %s" % (atype,))

def clear_auth(request):
    logging.info("Logging out")
    request.session.pop('write_auth', None)
    request.session.pop('read_auth', None)

    # Redirect in session?
    next = request.session.pop('next', None)
    if next:
        return HttpResponseRedirect(next)
    else:
        # If not, very bare confirmation:
        return HttpResponse("<html><head><title>Logged out</title></head><body><h1>Logged out</h1></body></html>")

