import json
import datetime
import logging

import markdown

from toolkit.util.ordereddict import OrderedDict

from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
import django.utils.timezone as timezone

from toolkit.diary.models import Showing, Event
from toolkit.diary.daterange import get_date_range

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def view_diary(request, year=None, month=None, day=None, event_type=None):
    # Returns public diary view, starting at specified year/month/day, filtered by
    # event type.
    #
    # Returns different things depending on the supplied parameters;
    # - if only year is passed, and no daysahead parameter,listings for the
    #   whole of that year
    # - if only year & month passed, and no daysahead parameter, listings for
    #   the whole of that month
    # - if year, month & day, and no daysahead parameter, listings for that day
    #   only
    # - if dayssahead parameter is passed, that many days from the specified
    #   year/month/date
    context = {}
    query_days_ahead = request.GET.get('daysahead', None)

    # Shared utility method to parse HTTP parameters and return a date range
    startdate, days_ahead = get_date_range(year, month, day, query_days_ahead)
    if startdate is None:
        raise Http404(days_ahead)
    enddate = startdate + datetime.timedelta(days=days_ahead)

    # Start getting together data to send to the template...

    context['today'] = datetime.date.today()
    context['start'] = startdate

    # Set page title
    if year:
        # If some specific dates were provided, use those
        context['event_list_name'] = u"Cube Programme for {0}".format(
            u"/".join([str(s) for s in (day, month, year) if s])
        )
    else:
        # Default title
        context['event_list_name'] = "Cube Programme"

    # Build query. The select_related() and prefetch_related on the end encourages
    # it to get the associated showing/event data, to reduce the number of SQL
    # queries
    showings = (Showing.objects.filter(confirmed=True)
                               .filter(hide_in_programme=False)
                               .filter(start__range=[startdate, enddate])
                               .filter(event__private=False)
                               .order_by('start')
                               .select_related()
                               .prefetch_related('event__media'))
    if event_type:
        showings = showings.filter(event__tags__name=event_type)

    # Build a list of events for that list of showings:
    events = OrderedDict()
    for showing in showings:
        events.setdefault(showing.event, set()).add(showing)

    context['showings'] = showings  # Set of Showing objects for date range
    context['events'] = events  # Ordered dict event -> set(showings)
    # This is prepended to filepaths from the MediaPaths table to use
    # as a location for images:
    context['media_url'] = settings.MEDIA_URL

    return render(request, 'view_showing_index.html', context)


def view_diary_json(request, year, month, day):
    # Used by the experimental new index; returns a JSON object containing
    # various bits of data about the events on the given year/month/day

    context = {}

    # Parse parameters:
    try:
        year = int(year) if year else None
        month = int(month) if month else None
        day = int(day) if day else None
    except ValueError:
        logger.error(u"Invalid value in date range, one of day {0}, month {1}, year {2}".format(day, month, year))
        raise Http404("Invalid values")

    startdatetime = timezone.get_current_timezone().localize(
        datetime.datetime(year, month, day)
    )
    enddatetime = startdatetime + datetime.timedelta(days=1)

    context['start'] = startdatetime

    # Do query. select_related() on the end encourages it to get the
    # associated showing/event data, to reduce the number of SQL queries
    showings = (Showing.objects.filter(confirmed=True)
                               .filter(hide_in_programme=False)
                               .filter(start__range=[startdatetime, enddatetime])
                               .filter(event__private=False)
                               .order_by('start')
                               .select_related()
                               .prefetch_related('event__media'))
    results = []
    # Build list of factoids to send back
    for showing in showings:
        event = showing.event

        results.append({
            'start': showing.start.strftime('%d/%m/%Y %H:%M'),
            'name': event.name,
            'copy': markdown.markdown(event.copy),
            'link': reverse("single-event-view", kwargs={'event_id': showing.event_id}),
            'image': event.media.all()[0].thumbnail.url if event.media.count() >= 1 else None,
            'tags': ", ".join(n[0] for n in event.tags.values_list('name')),
        })

    return HttpResponse(json.dumps(results), mimetype="application/json")


def view_showing(request, showing_id=None):
    # Show details of an individual showing, with given showing_id
    context = {}
    context['showing'] = get_object_or_404(Showing, id=showing_id)
    context['event'] = context['showing'].event
    return render(request, 'view_showing.html', context)


def view_event(request, event_id=None, legacy_id=None):
    # Show details of an individual event, with given event_id. Also allows
    # lookup by 'legacy_id', the non-primary key id used in the old toolkit.
    context = {}
    if event_id:
        event = get_object_or_404(Event, id=event_id)
    else:
        event = get_object_or_404(Event, legacy_id=legacy_id)
    media = event.media.all()[0] if len(event.media.all()) > 0 else None

    context = {
        'event': event,
        'showings': event.showings.all(),
        'media': {event.id: media},
        'media_url': settings.MEDIA_URL
    }
    return render(request, 'view_event.html', context)
