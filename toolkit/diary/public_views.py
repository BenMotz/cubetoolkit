import json
import datetime
import logging

from toolkit.util.ordereddict import OrderedDict

from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.safestring import mark_for_escaping
import django.utils.timezone as timezone
import django.views.generic as generic

from easy_thumbnails.files import get_thumbnailer

from toolkit.diary.models import Showing, Event
from toolkit.diary.daterange import get_date_range
from toolkit.diary.forms import SearchForm

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
    context['end'] = enddate
    # Following is user input passed back, so make doubly sure that it gets
    # escaped in the template:
    context['event_type'] = mark_for_escaping(event_type) if event_type else None

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
    showings = (Showing.objects.public()
                               .start_in_range(startdate, enddate)
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

    if request.GET.get('template'):
        return render(request, 'view_showing_index_oto.html', context)

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
    showings = (Showing.objects.public()
                               .start_in_range(startdatetime, enddatetime)
                               .order_by('start')
                               .select_related()
                               .prefetch_related('event__media'))
    results = []
    # Build list of factoids to send back
    for showing in showings:
        event = showing.event

        thumbnail = None
        media_item = event.get_main_mediaitem()
        if media_item:
            try:
                thumbnailer = get_thumbnailer(media_item.media_file)
                thumbnail = thumbnailer.get_thumbnail({
                    'size': (0, 200),
                    'crop': 'scale',
                    'upscale': True,
                }).url
            except Exception:
                logger.exception("Failed getting thumbnail for event {0}".format(event))

        results.append({
            'start': timezone.localtime(showing.start).strftime('%d/%m/%Y %H:%M'),
            'name': event.name,
            'copy': event.copy_html,
            'link': reverse("single-event-view", kwargs={'event_id': showing.event_id}),
            'image': thumbnail,
            'tags': ", ".join(n[0] for n in event.tags.values_list('name')),
        })

    return HttpResponse(json.dumps(results), mimetype="application/json")


def view_showing(request, showing_id=None):
    # Show details of an individual showing, with given showing_id
    # For now, just turn it into a view of the corresponding event:

    # Ensure that showing is only displayed if it's visible to the public:
    showings = Showing.objects.public().filter(id=showing_id)
    if len(showings) == 0:
        raise Http404("Showing not found")

    return view_event(request, event_id=showings[0].event_id)


def view_event(request, event_id=None, legacy_id=None):
    # Show details of an individual event, with given event_id. Also allows
    # lookup by 'legacy_id', the non-primary key id used in the old toolkit.
    context = {}
    if event_id:
        event = get_object_or_404(Event, id=event_id)
    else:
        event = get_object_or_404(Event, legacy_id=legacy_id)

    media = event.get_main_mediaitem()
    showings = event.showings.public()

    if event.private or len(showings) == 0:
        raise Http404("Event not found")

    context = {
        'event': event,
        'showings': showings,
        'media': {event.id: media},
        'media_url': settings.MEDIA_URL
    }
    return render(request, 'view_event.html', context)


class ArchiveIndex(generic.ArchiveIndexView):
    # Limit to public events
    queryset = Showing.objects.public().select_related()

    date_field = 'start'
    template_name = 'showing_archive.html'


class ArchiveYear(generic.YearArchiveView):
    # Limit to public events (select_related heavily reduces query count)
    queryset = Showing.objects.public().select_related()

    date_field = 'start'
    template_name = 'showing_archive_year.html'

    def get_dated_queryset(self, *args, **kwargs):
        kwargs['ordering'] = 'start'

        return super(ArchiveYear, self).get_dated_queryset(*args, **kwargs)


class ArchiveMonth(generic.MonthArchiveView):
    # Limit to public events (select_related heavily reduces query count)
    queryset = Showing.objects.public().select_related()

    date_field = 'start'
    template_name = 'showing_archive_month.html'
    month_format = '%m'

    def get_dated_queryset(self, *args, **kwargs):
        kwargs['ordering'] = 'start'

        return super(ArchiveMonth, self).get_dated_queryset(*args, **kwargs)


class ArchiveSearch(generic.list.ListView, generic.edit.FormMixin):
    model = Showing
    template_name = 'showing_archive_search.html'
    form_class = SearchForm

    def get_form_kwargs(self):
        # Load form data from GET params. If no GET was supplied then pass
        # None into the form, otherwise it will generate an error to say that
        # some search parameters are required
        return {'data': self.request.GET if len(self.request.GET) else None}

    def get_context_data(self, **kwargs):
        # Put the form in the context data sent to the template
        context = super(ArchiveSearch, self).get_context_data(**kwargs)
        context.update({
            'form': self.form,
            'search_submitted': len(self.request.GET),
        })
        return context

    def get_queryset(self):
        # Build the queryset using the form data

        # If the form was not valid, return a blank queryset (i.e. don't do a
        # search)
        # (is_valid() includes a check that the form wasn't blank)
        if not self.form.is_valid():
            return ()

        # Data from the search form:
        options = self.form.cleaned_data

        # Start with a queryset containing all public showings:
        queryset = Showing.objects.public().select_related()

        if options['search_term']:
            if options['search_in_descriptions']:
                # If a search term was provided and "search descriptions"
                # was checked, filter on the event name and copy:
                queryset = queryset.filter(
                    Q(event__name__icontains=options['search_term'])
                    |
                    Q(event__copy__icontains=options['search_term'])
                )
            else:
                # Otherwise just the event name
                queryset = queryset.filter(event__name__icontains=options['search_term'])
        # Add extra filters if start/end date were specified:
        if options['start_date']:
            queryset = queryset.filter(start__gte=options['start_date'])
        if options['end_date']:
            queryset = queryset.filter(start__lte=options['end_date'])

        return queryset

    def get(self, request):
        self.form = self.get_form(self.form_class)

        # Rely on functionality from the generic view...
        return super(ArchiveSearch, self).get(request)
