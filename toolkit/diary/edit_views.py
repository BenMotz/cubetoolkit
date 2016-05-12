import json
import datetime
import logging

from toolkit.util.ordereddict import OrderedDict

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms.models import modelformset_factory
from django.contrib import messages
from django.views.generic import View
import django.template
import django.db
from django.db.models import Q
import django.utils.timezone as timezone
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.decorators import method_decorator
from django.utils.html import escape

from toolkit.diary.models import (Showing, Event, DiaryIdea, MediaItem,
                                  EventTemplate, EventTag, Role, RotaEntry,
                                  PrintedProgramme)
import toolkit.diary.forms as diary_forms
import toolkit.diary.edit_prefs as edit_prefs
import toolkit.members.tasks

# Shared utility method:
from toolkit.diary.daterange import get_date_range

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _return_to_editindex(request):
    # If the user has set the 'popup' preference, then close the popup
    # and reload the page that opened the popup. Otherwise just redirect to
    # the index.

    prefs = edit_prefs.get_preferences(request.session)
    # (nb: the pref is stored as 'true'/'false', not a python bool!)
    if prefs['popups'] == 'true':
        # Use a really, really dirty way to emulate the original functionality
        # and close the popped up window: return a hard-coded page that
        # contains javascript to close the open window and reload the source
        # page.
        return HttpResponse("<!DOCTYPE html><html>"
                            "<head><title>-</title></head>"
                            "<body onload='"
                            "try{self.close();}catch(e){}"
                            "try{parent.$.fancybox.close();}catch(e){}"
                            "try{opener.location.reload(true);}catch(e){}"
                            "'>Ok</body>"
                            "</html>")
    else:
        # Redirect to edit index
        return HttpResponseRedirect(reverse("default-edit"))


@permission_required('toolkit.write')
def cancel_edit(request):
    # Again, a dirty hack, used with the above method, used for the "Cancel"
    # link in forms, to either close the popup or just redirect to the edit
    # page
    return _return_to_editindex(request)


@permission_required('toolkit.read')
def edit_diary_list(request, year=None, day=None, month=None):
    # Basic "edit" list view. Logic about processing of year/month/day
    # parameters is basically the same as for the public diary view.
    #
    # The logic is a bit twisty, from the requirement to show list all dates
    # and 'ideas' fields in the range, even if they don't have any events in
    # them, yet.

    context = {}
    # Sort out date range to display

    # If the query contained the number of days ahead to show then retrieve it
    # and store it as the default for this session (so coming back to the page
    # will look the same)
    query_days_ahead = request.GET.get('daysahead', None)

    if query_days_ahead:
        edit_prefs.set_preference(request.session, 'daysahead', query_days_ahead)
        default_days_ahead = query_days_ahead
    else:
        default_days_ahead = int(edit_prefs.get_preference(request.session, 'daysahead'))

    # utility function, shared with public diary view
    startdatetime, days_ahead = get_date_range(year, month, day, query_days_ahead, default_days_ahead)
    startdate = startdatetime.date()
    if startdatetime is None:
        raise Http404(days_ahead)

    # Don't allow viewing of dates before today, to avoid editing of the past:
    local_now = timezone.localtime(timezone.now())
    if startdate < local_now.date():
        # Redirect to page with today as the start date:
        new_url = u"{0}?daysahead={1}".format(
            reverse('day-edit', kwargs={
                'year': local_now.year,
                'month': local_now.month,
                'day': local_now.day
            }),
            days_ahead
        )
        return HttpResponseRedirect(new_url)

    enddatetime = startdatetime + datetime.timedelta(days=days_ahead)

    # Get all showings in the date range
    showings = (Showing.objects.start_in_range(startdatetime, enddatetime)
                               .order_by('start').select_related())
    # Build two dicts, to hold the showings and the ideas. These dicts are
    # initially empty, and get filled in if there are actually showings or
    # ideas for those dates.
    # This is done so that if dates don't have ideas/showings they still get
    # shown in the list
    dates = OrderedDict()
    ideas = {startdate: ''}  # Actually, I lied: start of visible list is not
                             # neccesarily the 1st of the month, so make sure
                             # that it gets an 'IDEAS' link shown
    for days in xrange(days_ahead):
        # Iterate through every date in the visible range, creating a dict
        # entry for each
        day_in_range = startdatetime + datetime.timedelta(days=days)
        dates[day_in_range.date()] = []
        # If it's the 1st of the month, make sure there's an ideas entry
        if day_in_range.day == 1:
            ideas[day_in_range.date()] = ''
    # Now insert all the showings into the 'dates' dict
    for showing in showings:
        dates[showing.start.date()].append(showing)
    # Dates without a showing will still be in the dates dict, so will still
    # be shown

    # Now get all 'ideas' in date range. Fiddle the date range to be from the
    # start of the month in startdate, so the idea for that month gets
    # included:
    idea_startdate = datetime.date(day=1, month=startdate.month, year=startdate.year)
    idea_list = (DiaryIdea.objects.filter(month__range=[idea_startdate, enddatetime])
                                  .order_by('month').select_related())
    # Assemble into the idea dict, with keys that will match the keys in the
    # showings dict
    for idea in idea_list:
        ideas[idea.month] = idea.ideas
    # Fiddle so that the idea for the first month is displayed, even if
    # startdate is after the first day of the month:
    if (idea_startdate not in showings and
            len(idea_list) > 0 and
            idea_list[0].month.month == startdate.month):
        ideas[startdate] = idea_list[0].ideas

    context['ideas'] = ideas
    context['dates'] = dates
    # Page title:
    context['event_list_name'] = u"Diary for {0} to {1}".format(
        startdatetime.strftime("%d-%m-%Y"),
        enddatetime.strftime("%d-%m-%Y")
    )
    context['start'] = startdatetime
    context['end'] = enddatetime
    context['edit_prefs'] = edit_prefs.get_preferences(request.session)
    return render(request, 'edit_event_index.html', context)

@permission_required('toolkit.read')
def edit_diary_data(request):
    date_format = "%Y-%m-%d"

    try:
        start_raw = request.GET.get('start', None)
        end_raw = request.GET.get('end', None)
        start = datetime.datetime.strptime(start_raw, date_format)
        end = datetime.datetime.strptime(end_raw, date_format)
        print start,end
    except ValueError:
        logger.error(
            u"Invalid value in date range, one of start '{0}' or end, '{1}"
            .format(start_raw, end_raw)
        )
        raise Http404("Invalid request")

    current_tz = timezone.get_current_timezone()
    start_in_tz = current_tz.localize(start)
    end_in_tz = current_tz.localize(end)

    showings = (Showing.objects.start_in_range(start_in_tz, end_in_tz)
                               .order_by('start')
                               .select_related())

    local_now = timezone.localtime(timezone.now())

    results = []
    for showing in showings:
        # For showings in the future, go to the edit showing page, for showings
        # in the past, show the event information (which should have edit links
        # disabled, when I get around to it)
        if showing.start >= local_now:
            url = reverse("edit-showing", kwargs={'showing_id': showing.pk}),
        else:
            url = reverse("edit-event-details-view",
                          kwargs={'pk': showing.event_id})

        styles = []

        if showing.cancelled:
            styles.append("s_cancelled")
        if showing.discounted:
            styles.append("s_discounted")
        if showing.event.private:
            styles.append("s_private")
        if showing.event.outside_hire:
            styles.append("s_outside_hire")
        if showing.confirmed:
            color = "#FF9080" if showing.in_past() else "#C70040"
        else:
            color = "#E0CFCF"

        results.append({
            'id': showing.pk,
            'title': showing.event.name,
            'start': timezone.localtime(showing.start).isoformat(),
            'end': timezone.localtime(showing.end_time).isoformat(),
            'url': url,
            'className': styles,
            'color': color,
        })

    return HttpResponse(json.dumps(results),
                        content_type="application/json; charset=utf-8")


@permission_required('toolkit.read')
def edit_diary_calendar(request, year=None, month=None):
    if year and month:
        display_month = datetime.date(int(year), int(month), 1)
    elif year and not month:
        raise Http404("Need year and month")
    else:
        display_month = timezone.localtime(timezone.now()).date()

    context = {
        'display_month': display_month,
    }

    return render(request, 'edit_event_calendar_index.html', context)


@permission_required('toolkit.read')
def set_edit_preferences(request):
    # Store user preferences as specified in the request's GET variables,
    # and return a JSON object containing all current user preferences

    # Store updated prefs
    edit_prefs.set_preferences(request.session, request.GET)
    # Retrieve and return prefs:
    prefs = edit_prefs.get_preferences(request.session)
    return HttpResponse(json.dumps(prefs), content_type="application/json")


@permission_required('toolkit.write')
@require_POST
def add_showing(request, event_id):
    # Add a showing to an existing event. Must be called via POST. Uses POSTed
    # data to create a new showing.
    # Must be called with a "copy_from" GET parameter. Showing options that
    # are not specified on the form (rota entries, confirmed/cancelled/etc) are
    # copied from the showing with the given ID.
    #
    # If add was successful, calls _return_to_editindex. On error goes to
    # form_showing.html

    # Although the data was POSTed, the copy_from is passed in the qyery:
    copy_from = request.GET.get('copy_from', None)

    try:
        copy_from_pk = int(copy_from, 10)
        source_showing = Showing.objects.get(pk=copy_from_pk)
        target_event_id = int(event_id, 10)
    except (TypeError, ValueError, django.core.exceptions.ObjectDoesNotExist) as err:
        logger.error(u"Failed getting object for showing clone operation: {0}".format(err))
        raise Http404("Requested source showing for clone not found")

    if source_showing.event_id != target_event_id:
        logger.error("Cloned showing event ID != URL event id")
        raise Http404("Requested source showing not associated with given event id")

    # Create form using submitted data:
    clone_showing_form = diary_forms.CloneShowingForm(request.POST)
    if clone_showing_form.is_valid():
        # Submitted data will have basic time & canceled/private info, but need
        # to set the event id and rota information manually, so don't commit
        # the new object immediately:
        new_showing = toolkit.diary.models.Showing(copy_from=source_showing)
        new_showing.start = clone_showing_form.cleaned_data['clone_start']
        new_showing.booked_by = clone_showing_form.cleaned_data['booked_by']
        # Need to save showing before cloning the rota, as the rota entries
        # need the key of the Showing, and that won't get created until the
        # Showing is saved...
        new_showing.save()
        new_showing.clone_rota_from_showing(source_showing)
        messages.add_message(
            request, messages.SUCCESS, u"Added showing on {0} for event '{1}'".format(
                new_showing.start.strftime("%d/%m/%y at %H:%M"),
                new_showing.event.name
            )
        )

        return _return_to_editindex(request)
    else:
        # For now, assume this is being called from "edit showing"
        # form, and return that
        showing = get_object_or_404(Showing, pk=copy_from)
        showing_form = diary_forms.ShowingForm(instance=showing)
        context = {
            'showing': showing,
            'form': showing_form,
            'clone_showing_form': clone_showing_form,
        }
        return render(request, 'form_showing.html', context)


@permission_required('toolkit.write')
@require_http_methods(["GET", "POST"])
def add_event(request):
    # Called GET, with a "date" parameter of the form day-month-year:
    #     returns 'form_new_event_and_showing' with given date filled in.
    # Called POST, with various data in request:
    #     creates new event, and number_of_showings, calls return_to_editindex
    #

    if request.method == 'POST':
        # Get event data, plus template and showing time and number of showing
        # days from form. Uses template to set rota roles and tags.
        form = diary_forms.NewEventForm(request.POST)
        if form.is_valid():
            # Event constructor will pull things from the template as
            # appropriate (excluding many/many relation which can only be set
            # after saving)
            new_event = Event(name=form.cleaned_data['event_name'],
                              template=form.cleaned_data['event_template'],
                              duration=form.cleaned_data['duration'],
                              outside_hire=form.cleaned_data['outside_hire'],
                              private=form.cleaned_data['private'])
            # Set event tags to those from its template:
            new_event.save()
            new_event.reset_tags_to_default()
            # create number_of_days showings, each offset by one more from the
            # date/time given in start parameter, and each with rota roles from
            # the template
            start = form.cleaned_data['start']
            for day_count in range(0, form.cleaned_data['number_of_days']):
                day_offset = datetime.timedelta(days=day_count)
                new_showing = Showing(event=new_event,
                                      start=(start + day_offset),
                                      discounted=form.cleaned_data['discounted'],
                                      confirmed=form.cleaned_data['confirmed'],
                                      booked_by=form.cleaned_data['booked_by'],
                                      )
                new_showing.save()
                # Set showing roles to those from its template:
                new_showing.reset_rota_to_default()

            messages.add_message(
                request, messages.SUCCESS, u"Added event '{0}' with showing on {1}".format(
                    new_event.name, new_showing.start.strftime("%d/%m/%y at %H:%M")
                )
            )
            return _return_to_editindex(request)
        else:
            # If form was not valid, re-render the form (which will highlight
            # errors)
            context = {'form': form}
            return render(request, 'form_new_event_and_showing.html', context)

    elif request.method == 'GET':
        # GET: Show form blank, with date filled in from GET date parameter:
        # Marshal date out of the GET request:
        default_date = django.utils.timezone.now().date() + datetime.timedelta(1)
        date = request.GET.get('date', default_date.strftime("%d-%m-%Y"))
        date = date.split("-")
        if len(date) != 3:
            return HttpResponse("Invalid start date", status=400, content_type="text/plain")
        try:
            date[0] = int(date[0], 10)
            date[1] = int(date[1], 10)
            date[2] = int(date[2], 10)
            event_start = timezone.get_current_timezone().localize(
                datetime.datetime(hour=20, minute=0, day=date[0], month=date[1], year=date[2])
            )
        except (ValueError, TypeError):
            return HttpResponse("Illegal date", status=400, content_type="text/plain")
        # Create form, render template:
        form = diary_forms.NewEventForm(initial={'start': event_start})
        context = {'form': form}
        return render(request, 'form_new_event_and_showing.html', context)


@permission_required('toolkit.write')
@require_http_methods(["GET", "POST"])
def edit_showing(request, showing_id=None):
    showing = get_object_or_404(Showing, pk=showing_id)

    RotaForm = diary_forms.rota_form_factory(showing)

    if request.method == 'POST':
        form = diary_forms.ShowingForm(request.POST, instance=showing)
        rota_form = RotaForm(request.POST)
        if showing.in_past():
            messages.add_message(request, messages.ERROR, "Can't edit showings that are in the past")
        elif form.is_valid() and rota_form.is_valid():
            # The rota form is separate; first save the updated showing
            modified_showing = form.save()
            # Then update the rota with the returned data:
            rota = rota_form.get_rota()
            modified_showing.update_rota(rota)

            messages.add_message(
                request, messages.SUCCESS, u"Updated showing for '{0}' at {1}".format(
                    showing.event.name, showing.start.strftime("%H:%M on %d/%m/%y")
                )
            )

            return _return_to_editindex(request)
    else:
        form = diary_forms.ShowingForm(instance=showing)
        rota_form = RotaForm()

    # Also create a form for "cloning" the showing (ie. adding another one),
    # but initialise it with values from existing event, but a day later...
    clone_showing_form = diary_forms.CloneShowingForm(
        initial={
            'clone_start': showing.start + datetime.timedelta(days=1)
        }
    )

    context = {
        'showing': showing,
        'form': form,
        'clone_showing_form': clone_showing_form,
        'rota_form': rota_form,
        'max_role_assignment_count': settings.MAX_COUNT_PER_ROLE,
    }

    return render(request, 'form_showing.html', context)


class EditEventView(View):
    """Handle the "edit event" form."""
    # Quite complex, so a class based view

    @method_decorator(permission_required('toolkit.write'))
    def dispatch(self, request, *args, **kwargs):
        return super(EditEventView, self).dispatch(request, *args, **kwargs)

    def _save(self, event, media_item, form, media_form):
        # Some factored out code: method is passed valid event and media form,
        # and commits the data.

        # When the form was created the copy was converted to HTML, so when
        # saved always clear the "legacy" flag:
        event.legacy_copy = False
        # Then save the main form:
        form.save()
        # Handle the media item form:
        if media_form.cleaned_data['media_file'] is False:
            # We get here if the "clear" checkbox was ticked.
            #
            # If we just call media_form.save then the MediaItem will have the
            # image removed - we're slightly repurposing the "clear" checkbox
            # to mean "remove the MediaItem from the event", NOT "remove the
            # image from the MediaItem":
            event.clear_main_mediaitem()
        elif media_form.cleaned_data['media_file'] is not None:
            # Get here if the form was submitted with the 'file' field not
            # blank
            #
            # Note that if the image is changed the old image is not deleted
            # from disk. This is Django's default behaviour, and matches what
            # the old toolkit used to do. No image thrown away!
            media_form.save()
            event.set_main_mediaitem(media_item)
        # If the media_form was submitted with blank file name/no data then
        # don't save it (caption is ignored)

    def post(self, request, event_id):
        # Handle POSTing of the "edit event" form. The slightly higher than
        # expected complexity is because there can be more than one media items
        # for an event (even though this isn't currently reflected in the UI).
        #
        # This means that there are two forms: one for the event, and one for
        # the media item. The extra logic is to cover the fact that both
        # records need to be updated.

        # Event object
        event = get_object_or_404(Event, pk=event_id)

        # Get the event's media item, or start a new one:
        media_item = event.get_main_mediaitem() or MediaItem()

        logger.info(u"Updating event {0}".format(event_id))
        # Create and populate forms:
        form = diary_forms.EventForm(request.POST, instance=event)
        media_form = diary_forms.MediaItemForm(request.POST, request.FILES, instance=media_item)

        # Validate
        if form.is_valid() and media_form.is_valid():
            self._save(event, media_item, form, media_form)
            messages.add_message(request, messages.SUCCESS, u"Updated details for event '{0}'".format(event.name))
            return _return_to_editindex(request)

        # Got here if there's a form validation error:
        context = {
            'event': event,
            'form': form,
            'media_form': media_form,
            'programme_copy_summary_max_chars': settings.PROGRAMME_COPY_SUMMARY_MAX_CHARS,
        }
        return render(request, 'form_event.html', context)

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        # For now only support a single media item:
        media_item = event.get_main_mediaitem() or MediaItem()

        # If the event has "legacy" (ie. non-html) copy then convert it to HTML;
        if event.legacy_copy:
            event.copy = event.copy_html

        form = diary_forms.EventForm(instance=event)
        media_form = diary_forms.MediaItemForm(instance=media_item)

        context = {
            'event': event,
            'form': form,
            'media_form': media_form,
            'programme_copy_summary_max_chars': settings.PROGRAMME_COPY_SUMMARY_MAX_CHARS,
        }

        return render(request, 'form_event.html', context)


@permission_required('toolkit.write')
def edit_ideas(request, year=None, month=None):
    # GET: return form for editing event for given month/year
    # POST: store editied idea, go back to edit list

    context = {}
    year = int(year)
    month = int(month)

    # Use get or create in order to silently create the ideas entry if it
    # didn't already exist:
    instance, _ = DiaryIdea.objects.get_or_create(
        month=datetime.date(year=year, month=month, day=1)
    )

    if request.method == 'POST':
        form = diary_forms.DiaryIdeaForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, u"Updated ideas for {0}/{1}".format(month, year))
            return _return_to_editindex(request)
    else:
        form = diary_forms.DiaryIdeaForm(instance=instance)

    context['form'] = form
    context['month'] = instance.month

    return render(request, 'form_idea.html', context)


@permission_required('toolkit.write')
@require_POST
def delete_showing(request, showing_id):
    # Delete the given showing

    showing = Showing.objects.get(pk=showing_id)
    if showing.in_past():
        logger.error(u"Attempted to delete showing id {0} that has already started/finished".format(showing_id))
        messages.add_message(request, messages.ERROR, "Can't delete showings that are in the past")
        return HttpResponseRedirect(
            reverse("edit-showing", kwargs={'showing_id': showing_id})
        )
    else:
        logging.info(u"Deleting showing id {0} (for event id {1})".format(showing_id, showing.event_id))
        messages.add_message(
            request, messages.SUCCESS, u"Deleted showing for '{0}' on {1}".format(
                showing.event.name, showing.start.strftime("%d/%m/%y")
            )
        )
        showing.delete()

    return _return_to_editindex(request)


@permission_required('toolkit.read')
def view_event_field(request, field, year, month, day):
    # Method shared across various (slightly primitive) views into event data;
    # the copy, terms and rota reports.
    #
    # This method gets the list of events for the given date range (using the
    # same shared logic for parsing the parameters as the public list / edit
    # list) and then uses the appropriate template to render the results.

    assert field in ('copy', 'terms', 'rota', 'copy_summary')

    query_days_ahead = request.GET.get('daysahead', None)
    start_date, days_ahead = get_date_range(year, month, day, query_days_ahead)
    if start_date is None:
        raise Http404(days_ahead)
    end_date = start_date + datetime.timedelta(days=days_ahead)
    showings = (Showing.objects.not_cancelled()
                               .confirmed()
                               .start_in_range(start_date, end_date)
                               .order_by('start')
                               # following prefetch is for the rota view
                               .prefetch_related('rotaentry_set__role')
                               .select_related())

    search = request.GET.get('search')
    if search:
        logging.info(u"Search term: {0}".format(search))
        # Note slightly sneaky use of **; this effectively results in a method
        # call like: showings.filter(event__copy__icontains=search)
        showings = showings.filter(
            Q(**{'event__' + field + '__icontains': search}) |
            Q(event__name__icontains=search)
        )

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'days_ahead': days_ahead,
        'showings': showings,
        'event_field': field,
        'search': search,
    }

    return render(request, u'view_{0}.html'.format(field), context)


@permission_required('toolkit.write')
def edit_event_templates(request):
    # View for editing event templates.
    # GET: Render multiple forms (using a formset)
    # POST: Update formset

    event_template_formset = modelformset_factory(
        EventTemplate,
        fields=('name', 'roles', 'tags', 'pricing'),
        can_delete=True)

    if request.method == 'POST':
        formset = event_template_formset(request.POST)
        if formset.is_valid():
            logger.info("Event templates updated")
            formset.save()
            # Reset formset, so get another blank one at the
            # end, deleted ones disappera, etc.
            formset = event_template_formset()
            messages.add_message(request, messages.SUCCESS, "Event templates updated")
    else:
        formset = event_template_formset()
    context = {'formset': formset}

    return render(request, 'edit_event_templates.html', context)


@permission_required('toolkit.write')
def edit_event_tags(request):
    # View for editing event tags.
    # GET: Reads tags and renders the (JavaScript based) template
    # POST: Process list of tags. Expected to be submitted via AJAX, retuns
    # json.
    tags = EventTag.objects.all()

    if request.method != 'POST':
        context = {'tags': tags}
        return render(request, 'edit_event_tags.html', context)

    errors = {}

    # Retrieve posted data:
    new_tag_names = request.POST.getlist('new_tags[]', [])
    deleted_tag_keys = request.POST.getlist('deleted_tags[]', [])
    # Ensure keys are all integers
    deleted_tag_keys = [int(k) for k in deleted_tag_keys]

    # process new tags:
    for new_tag in new_tag_names:
        tag_form = diary_forms.TagForm({'name': new_tag, 'readonly': False})
        if tag_form.is_valid():
            logger.info(u"Creating new tag {0}".format(
                tag_form.cleaned_data['name']))
            tag_form.save()
        else:
            errors[new_tag] = [
                u",".join(msg) for msg in tag_form.errors.itervalues()
            ]

    if errors:
        # Bail out before deleting anything
        return HttpResponse(
            json.dumps({'failed': True, 'errors': errors}),
            content_type="application/json"
        )

    # process deleted tags
    for deleted_key in deleted_tag_keys:
        try:
            tag = EventTag.objects.get(id=deleted_key)
        except EventTag.DoesNotExist:
            err = "Tag with key {0} can't be deleted: not found".format(deleted_key)
            errors.setdefault('delete', []).append(err)
            logger.error(err)
        else:
            logger.info(u"Deleting tag {0} (key {1})".format(tag.name, tag.pk))
            tag.delete()

    return HttpResponse(
        json.dumps({'failed': bool(errors), 'errors': errors}),
        content_type="application/json"
    )


@permission_required('toolkit.write')
def edit_roles(request):
    # This is pretty slow,but it's not a commonly used bit of the UI...
    # (To be precise, save involves >120 queries. This is because I've been
    # lazy and used the formset save method)

    RoleFormset = modelformset_factory(
            Role,
            diary_forms.RoleForm,
            fields=('name', 'standard',),
            can_delete=True)

    if request.method == 'POST':
        formset = RoleFormset(request.POST)
        if formset.is_valid():
            logger.info("Roles updated")
            formset.save()
            # Reset formset, so get another blank one at the
            # end, deleted ones disappear, etc.
            formset = RoleFormset()
            messages.add_message(request, messages.SUCCESS, "Roles updated")
    else:
        formset = RoleFormset()

    return render(request, 'form_edit_roles.html', {'formset': formset})


@permission_required('toolkit.write')
def printed_programme_edit(request, operation):
    assert operation in ('edit', 'add')

    programme_queryset = PrintedProgramme.objects.order_by('month')
    programme_formset = modelformset_factory(
        PrintedProgramme,
        fields=('programme', 'designer', 'notes'),
        can_delete=True,
        extra=0)

    # Blank forms, for use in GET or for whichever form hasn't been POSTed
    formset = programme_formset(queryset=programme_queryset)
    new_programme_form = diary_forms.NewPrintedProgrammeForm()

    if request.method == 'POST':
        if operation == "edit":
            formset = programme_formset(request.POST,
                                        request.FILES,
                                        queryset=programme_queryset)
            edited_form = formset
        elif operation == "add":
            new_programme_form = diary_forms.NewPrintedProgrammeForm(request.POST,
                                                                     request.FILES)
            edited_form = new_programme_form

        if edited_form.is_valid():
            edited_form.save()
            logger.info("Printed programme archive updated")
            return HttpResponseRedirect(reverse("edit-printed-programmes"))

    context = {
        'formset': formset,
        'new_programme_form': new_programme_form,
    }

    return render(request, 'form_printedprogramme_archive.html', context)


@permission_required('toolkit.read')
def view_rota_vacancies(request):
    days_ahead = 6
    start = timezone.now()
    end_date = start + datetime.timedelta(days=days_ahead)
    showings = (Showing.objects.not_cancelled()
                               .confirmed()
                               .start_in_range(start, end_date)
                               .order_by('start')
                               .prefetch_related('rotaentry_set__role')
                               .select_related())
    showings_vacant_roles = OrderedDict(
        (
            showing,
            showing.rotaentry_set.filter(Q(name="") | Q(name__isnull=True))
        ) for showing in showings
    )

    # Surprisingly round-about way to get tomorrow's date:
    now_local = django.utils.timezone.localtime(django.utils.timezone.now())

    context = {
        'days_ahead': days_ahead,
        'now': now_local,
        'now_plus_1d': now_local + datetime.timedelta(days=1),
        'rota_edit_url': request.build_absolute_uri(reverse("rota-edit")),
        'showings_vacant_roles': showings_vacant_roles,
    }

    return render(request, u'view_rota_vacancies.html', context)


class EditRotaView(View):
    """Handle the "edit rota" page."""

    # The following ensure that a user with the correct permission is logged in:
    @method_decorator(permission_required('diary.change_rotaentry'))
    def dispatch(self, request, *args, **kwargs):
        return super(EditRotaView, self).dispatch(request, *args, **kwargs)

    def get(self, request, year=None, day=None, month=None):
        # Fiddly way to set startdate to the start of the local day:
        # Get current UTC time and convert to local time:
        now_local = django.utils.timezone.localtime(django.utils.timezone.now())
        # Create a new local time with hour/min/sec set to zero:
        current_tz = django.utils.timezone.get_current_timezone()
        today_local_date = current_tz.localize(datetime.datetime(
            now_local.year, now_local.month, now_local.day))
        yesterday_local_date = today_local_date - datetime.timedelta(days=1)

        query_days_ahead = request.GET.get('daysahead', None)
        start_date, days_ahead = get_date_range(
            year, month, day, query_days_ahead, default_days_ahead=30)

        # Don't allow data from before yesterday to be displayed:
        if start_date < yesterday_local_date:
            start_date = yesterday_local_date

        end_date = start_date + datetime.timedelta(days=days_ahead)
        showings = (Showing.objects.not_cancelled()
                                   .confirmed()
                                   .start_in_range(start_date, end_date)
                                   .order_by('start')
                                   # force sane number of queries:
                                   .prefetch_related('rotaentry_set__role')
                                   .select_related())

        # Used by per-showing rota notes click to edit control:
        url_with_id = reverse('edit-showing-rota-notes', kwargs={'showing_id': 999})
        showing_notes_url_prefix = url_with_id[:url_with_id.find("999")]

        context = {
            'start_date': start_date,
            'end_date': end_date,
            'days_ahead': days_ahead,
            'showings': showings,
            'edit_showing_notes_url_prefix': showing_notes_url_prefix
        }

        return render(request, u'edit_rota.html', context)

    def post(self, request, year=None, day=None, month=None):
        # Get rota entry
        try:
            entry_id = int(request.POST[u'id'])
        except (ValueError, KeyError):
            logger.error("Invalid entry_id")
            return HttpResponse("Invalid entry id", status=400, content_type="text/plain")
        rota_entry = get_object_or_404(RotaEntry, pk=entry_id)

        # Check associated showing:
        if rota_entry.showing.in_past():
            return HttpResponse(u"Can't change rota for showings in the past",
                                status=403)

        # Get entered name, and store in rota entry:
        try:
            name = request.POST[u'value']
        except KeyError:
            return HttpResponse("Invalid request", status=400, content_type="text/plain")

        logger.info(u"Update role id {0} (#{1}) for showing {2} '{3}' -> '{4}' ({5})"
                    .format(rota_entry.role_id, rota_entry.rank,
                            rota_entry.showing_id, rota_entry.name, name,
                            rota_entry.pk))

        rota_entry.name = name
        rota_entry.save()

        response = escape(name)

        # Returned text is displayed as the rota entry:
        return HttpResponse(response, content_type="text/plain")


@permission_required('diary.change_rotaentry')
@require_POST
def edit_showing_rota_notes(request, showing_id):
    showing = get_object_or_404(Showing, pk=showing_id)
    form = diary_forms.ShowingRotaNotesForm(request.POST, instance=showing)

    if showing.in_past():
        return HttpResponse(u"Can't change rota for showings in the past",
                            status=403)
    elif form.is_valid():
        form.save()
    else:
        logger.error("Rota notes edit form not valid!")
        return HttpResponse("Unknown error", status=500, content_type="text/plain")

    response = escape(showing.rota_notes)

    return HttpResponse(escape(response), content_type="text/plain")


@permission_required('toolkit.write')
def view_force_error(request):
    raise AssertionError("Forced exception")
