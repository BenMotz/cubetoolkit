import datetime
import calendar
import logging

import django.core.exceptions
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404

from cube.diary.models import Showing, Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def view_diary(request, year=None, month=None, day=None):
    context = { }
    days_ahead = None


    if day is not None and month is None:
        raise Http404("Invalid request; cant specify day and no month")

    try:
        year = int(year) if year else None
        month = int(month) if month else None
        day = int(day) if day else None
    except ValueError:
        raise Http404("Invalid values")

    logger.debug("view_diary: day %s, month %s, year %s, span %s days", str(day), str(month), str(year), str(days_ahead))


    if day:
        startdate = datetime.datetime(year, month, day)
        days_ahead = 1
    elif month:
        startdate = datetime.datetime(year, month, 1)
        days_ahead = calendar.monthrange(year, month)[1]
    elif year:
        startdate = datetime.datetime(year, 1, 1)
        days_ahead = 365
        if calendar.isleap(year):
            days_ahead += 1 
    else:
        startdate = datetime.date.today()
        days_ahead = 30 # default

    # If days_ahead was provided in the request, use that instead of default
    if 'daysahead' in request.GET:
        try:
            days_ahead = int(request.GET['daysahead'], 10)
        except (ValueError, TypeError):
            pass

    enddate = startdate + datetime.timedelta(days=days_ahead)

    context['today'] = datetime.date.today()
    context['start'] = startdate
    context['event_list_name'] = "Events for %s" % "/".join( [ str(s) for s in (day, month, year) if s ])
    # Do query:
    context['showings'] = Showing.objects.filter(confirmed=True).filter(hide_in_programme=False).filter(start__range=[startdate, enddate]).filter(event__private=False).order_by('start')

    return render_to_response('indexed_showing_list.html', context)

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


