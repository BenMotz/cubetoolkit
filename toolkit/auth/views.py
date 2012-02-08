import logging

import bcrypt

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
import django.conf

from django import forms

class AuthForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput)

def _check_credentials(user, password, authtype):
    if authtype not in django.conf.settings.CUBE_AUTH:
        logging.error("Illegal authtype %s", authtype)
        return False
    logging.info("Credential check for %s with username %s", authtype, user)

    u_hash, p_hash = django.conf.settings.CUBE_AUTH[authtype]

    if p_hash == bcrypt.hashpw(password, p_hash) and u_hash == bcrypt.hashpw(user, u_hash):
        logging.info("Login sucess")
        return True
    else:
        logging.info("Login failed")
        return False

def auth(request, atype):

    if atype not in ('read', 'write'):
        raise Http404('Invalid auth requested')
    session_key = atype + '_auth'

    context = { 'atype' : atype, }
    # Already authorised?
    auth = request.session.get(session_key, False)

    form = None
    if request.method == 'POST':
        # Try to become authorised
        form = AuthForm(request.POST)
        if form.is_valid():
            if _check_credentials(form.cleaned_data['username'], form.cleaned_data['password'], atype):
                request.session[session_key] = True
                auth = True
            else:
                context['message'] = "Unrecognised username/password for %s access" % (atype,)

    if auth:
        next = request.session.pop('next', None) or reverse("default-view")
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

