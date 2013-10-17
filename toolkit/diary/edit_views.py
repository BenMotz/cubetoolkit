import re
import json
import datetime
import logging

from toolkit.util.ordereddict import OrderedDict

import celery.result

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms.models import modelformset_factory
from django.contrib import messages
import django.template
import django.db
from django.db.models import Q
import django.utils.timezone as timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from toolkit.diary.models import (Showing, Event, DiaryIdea, MediaItem,
                                  EventTemplate, EventTag, Role)
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
        # Use a really, really dirty way to emulate the original functionality and
        # close the popped up window: return a hard-coded page that contains
        # javacsript to close the open window and reload the source page.
        return HttpResponse("<!DOCTYPE html><html>"
                            "<head><title>-</title></head>"
                            "<body onload='self.close(); opener.location.reload(true);'>Ok</body>"
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


@login_required
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
    # start of the month in startdate, so the idea for that month gets included:
    idea_startdate = datetime.date(day=1, month=startdate.month, year=startdate.year)
    idea_list = (DiaryIdea.objects.filter(month__range=[idea_startdate, enddatetime])
                                  .order_by('month').select_related())
    # Assemble into the idea dict, with keys that will match the keys in the
    # showings dict
    for idea in idea_list:
        ideas[idea.month] = idea.ideas
    # Fiddle so that the idea for the first month is displayed, even if
    # startdate is after the first day of the month:
    if (idea_startdate not in showings
            and len(idea_list) > 0
            and idea_list[0].month.month == startdate.month):
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


@login_required
def set_edit_preferences(request):
    # Store user preferences as specified in the request's GET variables,
    # and return a JSON object containing all current user preferences

    # Store updated prefs
    edit_prefs.set_preferences(request.session, request.GET)
    # Retrieve and return prefs:
    prefs = edit_prefs.get_preferences(request.session)
    return HttpResponse(json.dumps(prefs), mimetype="application/json")


@login_required
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
    except (TypeError, ValueError, django.core.exceptions.ObjectDoesNotExist) as err:
        logger.error(u"Failed getting object for showing clone operation: {0}".format(err))
        raise Http404("Requested source showing for clone not found")

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
            new_event = Event(name=form.cleaned_data['event_name'],
                              template=form.cleaned_data['event_template'],
                              duration=form.cleaned_data['duration'],
                              outside_hire=form.cleaned_data['external'],
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


def _edit_event_handle_post(request, event_id):
    # Handle POSTing of the "edit event" form. The slightly higher than expected
    # complexity is because there can be more than one media items for an event
    # (even though this isn't currently reflected in the UI).
    #
    # This means that there are two forms: one for the event, and one for the
    # media item. The extra logic is to cover the fact that both records need
    # to be updated.

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
        messages.add_message(request, messages.SUCCESS, u"Updated details for event '{0}'".format(event.name))
        # If the media_form was submitted with blank file name/no data then
        # don't save it (caption is ignored)
        return _return_to_editindex(request)

    # Got here if there's a form validation error:
    context = {
        'event': event,
        'form': form,
        'media_form': media_form,
    }
    return render(request, 'form_event.html', context)


@permission_required('toolkit.write')
def edit_event(request, event_id=None):
    # Event edit form. The 'POST' case, for submitting edits, is a bit of a
    # monster, and is a separate method

    # Handling of POST (ie updates) is factored out into a separate function
    if request.method == 'POST':
        return _edit_event_handle_post(request, event_id)

    # So now just dealing with a GET:
    event = get_object_or_404(Event, pk=event_id)
    # For now only support a single media item:
    if event.media.count() > 0:
        media_item = event.media.all()[0]
    else:
        media_item = MediaItem()

    # If the event has "legacy" (ie. non-html) copy then convert it to HTML;
    if event.legacy_copy:
        event.copy = event.copy_html

    form = diary_forms.EventForm(instance=event)
    media_form = diary_forms.MediaItemForm(instance=media_item)

    context = {
        'event': event,
        'form': form,
        'media_form': media_form,
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
    instance, created = DiaryIdea.objects.get_or_create(
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


@login_required
def view_event_field(request, field, year, month, day):
    # Method shared across various (slightly primitive) views into event data;
    # the copy, terms and rota reports.
    #
    # This method gets the list of events for the given date range (using the
    # same shared logic for parsing the parameters as the public list / edit
    # list) and then uses the appropriate template to render the results.

    logger.debug(u"view_event_field: field {0}".format(field))
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
                               .prefetch_related('rotaentry_set__role')  # mildly hacky optimisation for rota view
                               .select_related())

    search = request.GET.get('search')
    if search:
        logging.info(u"Search term: {0}".format(search))
        # Note slightly sneaky use of **; this effectively results in a method
        # call like: showings.filter(event__copy__icontains=search)
        showings = showings.filter(
            Q(**{'event__' + field + '__icontains': search})
            | Q(event__name__icontains=search)
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

    event_template_formset = modelformset_factory(EventTemplate, can_delete=True)

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
    # GET: Reads tags and renders the (JavaScript heavy) template
    # POST: Process list of tags. Expected to be submitted via AJAX, so doesn't
    #       return much.
    tags = EventTag.objects.all()

    if request.method != 'POST':
        context = {'tags': tags}
        return render(request, 'edit_event_tags.html', context)
    # Data was posted

    # First, pull out mapping of tag key : name
    # The form returns the data as a set of key/values where the keys are;
    # "tags[x]" where x is either a positive integer which is the key of an
    # existing tag, or a negative integer indicating that this is a new tag.
    # Tags to be deleted have their value set to '' (the empty string)
    tags_submitted = {}
    # regex to recognise the "tags[x]" format:
    tag_re = re.compile("^tags\[([-\d]+)\]$")
    for key, val in request.POST.iteritems():
        m = tag_re.match(key)
        if m:
            tags_submitted[int(m.group(1), 10)] = val.strip().lower()

    # Build dict of existing tags:
    tags_by_pk = dict((tag.pk, tag) for tag in tags)
    # Now update / add as appropriate. Any tag keys that aren't included in
    # the update are deleted.
    for submitted_pk, submitted_name in tags_submitted.iteritems():
        extant_tag = tags_by_pk.pop(submitted_pk, None)
        if extant_tag:
            if submitted_name == '':
                logger.info(u"Deleting tag {0} (key {1})".format(extant_tag.name, extant_tag.pk))
                extant_tag.delete()
            elif extant_tag.name != submitted_name:
                logger.info(u"Changing name of tag id {0} from {1} to {2}"
                            .format(extant_tag.pk, extant_tag.name, submitted_name))
                extant_tag.name = submitted_name
                extant_tag.save()
        elif extant_tag is None:
            new_tag = EventTag(name=submitted_name)
            logger.info(u"Creating new tag {0}".format(submitted_name))
            # database constraints will enforce uniqueness of tag name
            try:
                new_tag.save()
            except django.db.IntegrityError as interr:
                logger.error(u"Failed adding tag {0}: {1}".format(submitted_name, interr))
    # There shouldn't be any tags left in tags_by_pk:
    if len(tags_by_pk) != 0:
        logger.error(u"Tag(s) {0} not included in update".format(",".join(tags_by_pk.values())))

    return HttpResponse("OK")


@permission_required('toolkit.write')
def edit_roles(request):
    # This is pretty slow,but it's not a commonly used bit of the UI...
    # (To be precise, save involves >120 queries. TThis is because I've been lazy
    # and used the formset save method)

    RoleFormset = modelformset_factory(Role, diary_forms.RoleForm, can_delete=True)

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


def _render_mailout_body(days_ahead):
    # Render default mail contents;

    # Read data
    start_date = timezone.now()
    end_date = start_date + datetime.timedelta(days=days_ahead)
    showings = (Showing.objects.public()
                               .not_cancelled()
                               .start_in_range(start_date, end_date)
                               .order_by('start')
                               .select_related()
                               .prefetch_related('event__showings'))

    # Render into mail template
    mail_template = django.template.loader.get_template("mailout_body.txt")

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'showings': showings,
    }

    return mail_template.render(django.template.Context(context))


def _render_mailout_form(request, body_text, subject_text):
    form = diary_forms.MailoutForm(initial={'subject': subject_text, 'body': body_text})
    email_count = (toolkit.members.models.Member.objects.filter(email__isnull=False)
                                                        .exclude(email='')
                                                        .exclude(mailout_failed=True)
                                                        .filter(mailout=True)
                                                        .count())
    context = {
        'form': form,
        'email_count': email_count,
    }

    return render(request, 'form_mailout.html', context)


@permission_required('toolkit.write')
@require_http_methods(["GET", "POST"])
def mailout(request):
    # This view loads a form with a draft mailout subject & body. When the user
    # is happy, they click "Send", which POSTs the data back to this view. If
    # the data pases the basic checks then it gets sent back in the
    # "mailout_send" form. That form has javascript which, if the user
    # confirms, posts to the "exec-mailout" view

    if request.method == 'GET':
        try:
            query_days_ahead = int(request.GET.get('daysahead', 9))
        except ValueError:
            query_days_ahead = 9
        body_text = _render_mailout_body(query_days_ahead)
        subject_text = "CUBE Microplex forthcoming events"
        return _render_mailout_form(request, body_text, subject_text)
    elif request.method == 'POST':
        form = diary_forms.MailoutForm(request.POST)
        if not form.is_valid():
            return render(request, 'form_mailout.html', {'form': form})
        return render(request, 'mailout_send.html', form.cleaned_data)


# @condition(etag_func=None, last_modified_func=None)
@permission_required('toolkit.write')
@require_POST
def exec_mailout(request):

    form = diary_forms.MailoutForm(request.POST)
    if not form.is_valid():
        logger.error("Mailout failed: {0}".format(repr(form.errors)))
        response = {
            'status': 'error',
            'errors': dict(form.errors),
        }
        return HttpResponse(json.dumps(response), mimetype="application/json")

    result = toolkit.members.tasks.send_mailout.delay(form.cleaned_data['subject'],
                                                      form.cleaned_data['body'])

    response = HttpResponse(
        json.dumps({'status': 'ok', 'task_id': result.task_id, 'progress': 0}),
        mimetype="application/json"
    )

    return response


@permission_required('toolkit.write')
@require_GET
def mailout_progress(request):
    async_result = celery.result.AsyncResult(id=request.GET['task_id'])
    state = async_result.state
    progress = 0
    complete = False
    # Following values are set if complete:
    error = None
    sent_count = None
    error_msg = None

    if state:
        progress_parts = state.split("PROGRESS")
        if len(progress_parts) > 1:
            try:
                progress = int(progress_parts[1])
            except ValueError:
                logger.error("Invalid progress from async mailout task: {0}".format(state))
        elif state == "SUCCESS":
            progress = 100
            complete = True
            if (async_result.result
                    and isinstance(async_result.result, tuple)
                    and len(async_result.result) == 3):
                error, sent_count, error_msg = async_result.result
            else:
                error = True
                sent_count = 0
                error_msg = u"Couldn't retrieve status from completed job"
        elif state == "FAILURE":
            complete = True
            error = True
            if async_result.result:
                error_msg = unicode(async_result.result)
            else:
                error_msg = "Failed: Unknown error"
        elif state == "PENDING":
            progress = 0
        else:
            logger.error(u"Invalid data from async mailout task: {0}".format(state))

    return HttpResponse(
        json.dumps({
            'task_id': async_result.task_id,
            'complete': complete,
            'progress': progress,
            'error': error,
            'error_msg': error_msg,
            'sent_count': sent_count,
        }),
        mimetype="application/json"
    )
