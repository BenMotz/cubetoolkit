import datetime
import calendar
import logging
from toolkit.ordereddict import OrderedDict

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from toolkit.diary.models import Showing, Event, DiaryIdea, RotaEntry
import toolkit.diary.forms

from toolkit.auth.decorators import require_read_auth, require_write_auth

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def _return_close_window():
    # Really, really dirty way to emulate the original functionality and
    # close the popped up window
    return HttpResponse("<!DOCTYPE html><html><head><title>-</title></head><body onload='self.close(); opener.location.reload(true);'>Ok</body></html>")


def _get_date_range(year, month, day, user_days_ahead):
    """Support method to take fields read from HTTP request and return a tuple
    (datetime, number_of_days)
    If month or day are blank, they default to 1. If all three are blank it 
    defaults to today"""
    if day is not None and month is None:
        raise Http404("Invalid request; cant specify day and no month")

    try:
        year = int(year) if year else None
        month = int(month) if month else None
        day = int(day) if day else None
    except ValueError:
        raise Http404("Invalid values")

    logger.debug("view_diary: day %s, month %s, year %s, span %s days", str(day), str(month), str(year), str(user_days_ahead))

    try:
        if day:
            startdate = datetime.date(year, month, day)
            days_ahead = 1
        elif month:
            startdate = datetime.date(year, month, 1)
            days_ahead = calendar.monthrange(year, month)[1]
        elif year:
            startdate = datetime.date(year, 1, 1)
            days_ahead = 365
            if calendar.isleap(year):
                days_ahead += 1 
        else:
            startdate = datetime.date.today()
            days_ahead = 30 # default
    except ValueError:
        raise Http404("Invalid date")

    if user_days_ahead:
        try:
            days_ahead = int(user_days_ahead)
        except (ValueError, TypeError):
            pass


    return startdate, days_ahead

def view_diary(request, year=None, month=None, day=None):
    context = { }
    query_days_ahead = request.GET.get('daysahead', None)
    startdate, days_ahead = _get_date_range(year, month, day, query_days_ahead)
    enddate = startdate + datetime.timedelta(days=days_ahead)

    context['today'] = datetime.date.today()
    context['start'] = startdate
    # Set page title
    if year:
        # If some specific dates were provided, use those
        context['event_list_name'] = "Events for %s" % "/".join( [ str(s) for s in (day, month, year) if s ])
    else:
        # Default title
        context['event_list_name'] = "Cube Programme"
    # Do query. select_related() on the end encourages it to get the
    # associated showing/event data, to reduce the number of SQL queries
    context['showings'] = Showing.objects.filter(confirmed=True).filter(hide_in_programme=False).filter(start__range=[startdate, enddate]).filter(event__private=False).order_by('start').select_related()

    return render_to_response('indexed_showing_list.html', context)

@require_read_auth
def edit_diary_list(request, year=None, day=None, month=None):
    context = { }
    # Sort out date range to display
    query_days_ahead = request.GET.get('daysahead', None)
    startdate, days_ahead = _get_date_range(year, month, day, query_days_ahead)
    # Don't allow viewing of dates before today, to avoid editing of the past:
    if startdate < datetime.date.today():
        # Change startdate to today:
        startdate = datetime.date.today()
        # Redirect to the correct page:
        new_url = ("%s?daysahead=%d" %
                    (reverse('day-edit', kwargs={
                               'year' : startdate.year,
                               'month' : startdate.month,
                               'day' : startdate.day}),
                     days_ahead))
        return HttpResponseRedirect(new_url)
    enddate = startdate + datetime.timedelta(days=days_ahead)


    # Get all showings in the date range
    showings = Showing.objects.filter(start__range=[startdate, enddate]).order_by('start').select_related()
    # Build a dict with all the dates in the range as keys and empty lists as values
    dates = OrderedDict([ ((startdate + datetime.timedelta(days=days)), []) for days in xrange(days_ahead) ])
    # Put showings in the dict (so days without showings will have an empty dict)
    for showing in showings:
        dates[showing.start.date()].append(showing)

    # Get all 'ideas' in date range. Fiddle the date range to be from the start
    # of the month in startdate, so the idea for that month gets included:
    idea_startdate = datetime.date(day=1, month=startdate.month, year=startdate.year)
    idea_list = DiaryIdea.objects.filter(month__range=[idea_startdate, enddate]).order_by('month').select_related()
    logging.info(str(idea_list))
    ideas = {}
    # Assemble into dict, with keys that will match the keys in the showings
    # dict
    for idea in idea_list:
        ideas[idea.month] = idea.ideas
    # Fiddle so that the idea for the first month is displayed, even if 
    # startdate is after the first day of the month:
    if idea_startdate not in showings and len(idea_list) > 0:
        ideas[startdate] = idea_list[0].ideas


    context['ideas'] = ideas
    context['dates'] = dates
    context['event_list_name'] = "Diary for %s to %s" % (str(startdate), str(enddate))
    context['start'] = startdate
    context['end'] = enddate

    return render_to_response('edit_list.html', context)

@require_read_auth
def add_showing(request, event_id):
    if request.method != 'POST':
        return HttpResponse('Invalid request!', 405) # 405 = Method not allowed
    copy_from = request.GET.get('copy_from', None)
    try:
        copy_from = int(copy_from, 10)
    except (TypeError, ValueError):
        copy_from = None

    # Create form using submitted data:
    form = toolkit.diary.forms.NewShowingForm(request.POST)
    if form.is_valid():
        # Submitted data will have basic time & canceled/private info, but need
        # to set the event id and rota information manually, so don't commit
        # the new object immediately:
        new_showing = form.save(commit=False)
        # Set event ID:
        new_showing.event_id = event_id
        # Create showing
        new_showing.save()
        # If a showing_id was supplied, clone the rota from that:
        if copy_from:
            source_showing = Showing.objects.get(pk=copy_from)
            for rota_entry in source_showing.rotaentry_set.all():
                r = RotaEntry(showing=new_showing, template=rota_entry)
                print "role_id:", r.role_id
                r.save()

        return _return_close_window()
    else:
        # If copy_from was supplied, assume being called from "edit showing"
        # form, and return that
        if copy_from:
            showing = get_object_or_404(Showing, pk=copy_from)
            showing_form = toolkit.diary.forms.ShowingForm(instance=showing)
            context = {
                    'showing' : showing,
                    'form' : showing_form,
                    'new_showing_form' : form,
                    }
            return render_to_response('form_showing.html', RequestContext(request, context))
        else:
            return HttpResponse("Failed adding showing", status=400)

@require_write_auth
def add_event(request):
    if request.method == 'POST':
        form = toolkit.diary.forms.NewEventForm(request.POST)
        if form.is_valid():
            new_event = Event(name=form.cleaned_data['event_name'],
                              etype=form.cleaned_data['event_type'],
                              duration=form.cleaned_data['duration'],
                              outside_hire=form.cleaned_data['external'],
                              private=form.cleaned_data['private'])
            new_event.save()
            showings = []
            start = form.cleaned_data['start']
            for n in range(0, form.cleaned_data['number_of_days']):
                day_offset = datetime.timedelta(days=n)
                new_showing = Showing(event=new_event,
                                      start=(start + day_offset),
                                      discounted=form.cleaned_data['discounted'],
                                      confirmed=form.cleaned_data['confirmed'],
                                      booked_by=form.cleaned_data['booked_by'],
                                      )
                new_showing.save()
                new_showing.reset_rota_to_default()
                showings.append(new_showing)
            return _return_close_window()
        else:
            context = { 'form' : form }
            return render_to_response('form_new_event_and_showing.html', RequestContext(request, context))
    elif request.method == 'GET':
        # Marshal date out of the GET request:
        date = request.GET.get('date', datetime.date.today().strftime("%d-%m-%Y"))
        date = date.split("-")
        assert(len(date) == 3) # Should probably do this better
        try:
            date[0] = int(date[0], 10)
            date[1] = int(date[1], 10)
            date[2] = int(date[2], 10)
            event_start = datetime.datetime(hour=20, minute=0, day=date[0], month=date[1], year=date[2])
        except (ValueError, TypeError):
            return HttpResponse("Illegal date", status=400)
        # Creat form, render template:
        form = toolkit.diary.forms.NewEventForm(initial={'start' : event_start})
        context = { 'form' : form }
        return render_to_response('form_new_event_and_showing.html', RequestContext(request, context))
    else:
        return HttpResponse("Illegal method", status=405)

@require_write_auth
def edit_showing(request, showing_id=None):
    showing = get_object_or_404(Showing, pk=showing_id)

    if request.method == 'POST':
        form = toolkit.diary.forms.ShowingForm(request.POST, instance=showing)
        if form.is_valid():
            # Because Django can't cope with updating the rota automatically
            # do this two-step commit=False / save thing, then manually wrangle
            # the rota:
            modified_showing = form.save(commit=False)
            modified_showing.save()
            # Now get list of selected roles;
            selected_roles = dict(request.POST)['roles']
            initial_set = set( r.values()[0] for r in showing.rotaentry_set.values('role_id'))
            print initial_set
            # For each id, this will get the entry or create it:
            for role_id in selected_roles:
                role_id = int(role_id)
                modified_showing.rotaentry_set.get_or_create(role_id = role_id)
                initial_set.discard(role_id)
            # Now remove any roles that we haven't seen:
            modified_showing.rotaentry_set.filter(role__in = initial_set).delete()

            return _return_close_window()
    else:
        form = toolkit.diary.forms.ShowingForm(instance=showing)
    # Also create a form for "cloning" the showing (ie. adding another one),
    # but initialise it with values from existing event, but a day later...
    new_showing_template = Showing.objects.get(pk=showing.pk)
    new_showing_template.pk = None
    new_showing_template.start += datetime.timedelta(days=1)
    new_showing_form = toolkit.diary.forms.NewShowingForm(instance=new_showing_template)

    context = {
            'showing' : showing,
            'form' : form,
            'new_showing_form' : new_showing_form,
            }

    return render_to_response('form_showing.html', RequestContext(request, context))


@require_write_auth
def edit_event(request, event_id=None):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        form = toolkit.diary.forms.EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return _return_close_window()
    else:
        form = toolkit.diary.forms.EventForm(instance=event)

    context = {
            'event' : event,
            'form' : form,
            }

    return render_to_response('form_event.html', RequestContext(request, context))

@require_write_auth
def edit_ideas(request, year=None, month=None):
    context = {}
    year = int(year)
    month = int(month)

    # Use get or create in order to silently create the ideas entry if it
    # didn't already exist:
    instance, created = DiaryIdea.objects.get_or_create(month=datetime.date(year=year, month=month, day=1))
    if request.method == 'POST':
        form = toolkit.diary.forms.DiaryIdeaForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return _return_close_window()
    else:
        form = toolkit.diary.forms.DiaryIdeaForm(instance=instance)

    context['form'] = form
    context['month'] = instance.month

    return render_to_response('form_idea.html', RequestContext(request, context))

def view_showing(request, showing_id=None):
    context = {}
    context['showing'] = get_object_or_404(Showing, id=showing_id)
    context['event'] = context['showing'].event
    return render_to_response('showing.html', context)

def view_event(request, event_id=None):
    context = {}
    context['event'] = get_object_or_404(Event, id=event_id)
    context['showings'] = context['event'].showing_set.all()
    return render_to_response('event.html', context)

@require_write_auth
def delete_showing(request, showing_id):
    if request.method == 'POST':
        showing = Showing.objects.get(pk=showing_id)
        showing.delete()

    return _return_close_window()

@require_read_auth
def view_rota(request, year, month, day):
    query_days_ahead = request.GET.get('daysahead', None)
    start_date, days_ahead = _get_date_range(year, month, day, query_days_ahead)
    end_date = start_date + datetime.timedelta(days=days_ahead)
    showings = Showing.objects.filter(cancelled=False).filter(confirmed=True).filter(start__range=[start_date, end_date]).order_by('start').select_related()
    context = {
            'showings': showings,
            }
    return render_to_response('rota_view.html', context)
