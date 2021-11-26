import json
import datetime
import logging

import six
import celery.result
import redis
import kombu.exceptions

from django.http import HttpResponse
from django.shortcuts import render
import django.template
import django.db
import django.utils.timezone as timezone
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods)
from django.conf import settings

from toolkit.diary.models import Showing
from toolkit.members.models import Member
import toolkit.diary.forms as diary_forms
import toolkit.members.tasks

# Shared utility method:

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _render_mailout_subject_and_body(days_ahead, copy_days_ahead):
    # Render default mail contents. Returns (subject, text mail, html mail)

    # Read data
    start_date = timezone.now()
    end_date = start_date + datetime.timedelta(days=days_ahead)
    copy_end_date = start_date + datetime.timedelta(days=copy_days_ahead)
    showings = (Showing.objects.public()
                               .not_cancelled()
                               .start_in_range(start_date, end_date)
                               .order_by('start')
                               .select_related()
                               .prefetch_related('event__showings'))

    event_ids = set()
    showings_once_per_event = []
    for s in showings.public().start_in_range(start_date, copy_end_date):
        if s.event_id not in event_ids:
            showings_once_per_event.append(s)
            event_ids.add(s.event_id)
    try:
        # %-d strips the leading 0 from the day of the month - as per the
        # python docs, this is platform specific to Linux / glibc. See
        # strftime(3).
        first_event_date = showings[0].start.strftime(' commencing %A %-d %B')
    except IndexError:  # Corner case for no events
        first_event_date = ''
    subject_text = "%s forthcoming events%s" % (
                    settings.VENUE['longname'], first_event_date)

    # Render into mail templates
    text_mail_template = django.template.loader.get_template(
        "mailout_body.txt")

    html_mail_template = django.template.loader.get_template(
        "mailout_body.html")

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'showings': showings,
        'showings_details': showings_once_per_event,
        'copy_days_ahead': copy_days_ahead,
        'site_url': settings.VENUE['url']
    }

    return (
        subject_text,
        text_mail_template.render(context),
        html_mail_template.render(context),
    )


def _render_mailout_form(request, body_text, body_html, subject_text, context):
    form = diary_forms.MailoutForm(
        html_mailout_enabled=settings.HTML_MAILOUT_ENABLED,
        initial={'subject': subject_text,
                 'body_text': body_text,
                 'body_html': body_html})
    email_count = (toolkit.members.models.Member.objects.mailout_recipients()
                                                        .count())
    context.update({
        'form': form,
        'email_count': email_count,
    })

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
        days_ahead = settings.MAILOUT_LISTINGS_DAYS_AHEAD
        copy_days_ahead = settings.MAILOUT_DETAILS_DAYS_AHEAD

        try:
            days_ahead = int(request.GET.get('daysahead', days_ahead))
            copy_days_ahead = int(
                    request.GET.get('copydaysahead', copy_days_ahead))
        except ValueError:
            pass
        subject_text, body_text, body_html = _render_mailout_subject_and_body(
                days_ahead, copy_days_ahead)
        context = {
            "days_ahead": days_ahead,
            "copy_days_ahead": copy_days_ahead
        }
        return _render_mailout_form(request, body_text, body_html,
                                    subject_text, context)
    elif request.method == 'POST':
        form = diary_forms.MailoutForm(
            request.POST,
            html_mailout_enabled=settings.HTML_MAILOUT_ENABLED)
        if not form.is_valid():
            return render(request, 'form_mailout.html', {'form': form})
        return render(request, 'mailout_send.html', form.cleaned_data)


# @condition(etag_func=None, last_modified_func=None)
@permission_required('toolkit.write')
@require_POST
def exec_mailout(request):
    form = diary_forms.MailoutForm(
        request.POST,
        html_mailout_enabled=settings.HTML_MAILOUT_ENABLED)
    if not form.is_valid():
        logger.error("Mailout failed: {0}".format(repr(form.errors)))
        response = {
            'status': 'error',
            'errors': dict(form.errors),
        }
        return HttpResponse(json.dumps(response),
                            content_type="application/json")

    if settings.HTML_MAILOUT_ENABLED and form.cleaned_data['send_html']:
        body_html = form.cleaned_data['body_html']
    else:
        body_html = None

    try:
        result = toolkit.members.tasks.send_mailout.delay(
            form.cleaned_data["subject"],
            form.cleaned_data["body_text"],
            body_html,
        )
    except kombu.exceptions.KombuError as kerr:
        logger.error("Failed starting mailout task: %s", kerr)
        return HttpResponse(
            json.dumps(
                {
                    "status": "error",
                    "complete": True,
                    "error": True,
                    "error_msg": "Failed starting task: %s" % str(kerr),
                }
            ),
            content_type="application/json",
        )
    else:
        response = HttpResponse(
            json.dumps(
                {"status": "ok", "task_id": result.task_id, "progress": 0}
            ),
            content_type="application/json",
        )

    return response


@permission_required('toolkit.write')
@require_POST
def mailout_test_send(request):
    # Essentially the same as the form for exec_mailout, but with an 'address'
    # field. Should really refactor to use the same form + a separate 'address'
    # form.
    form = diary_forms.MailoutTestForm(
        request.POST,
        html_mailout_enabled=settings.HTML_MAILOUT_ENABLED)
    if not form.is_valid():
        response = {
            'status': 'error',
            'errors': ", ".join(
                "%s: %s" % (k, v) for (k, v) in form.errors.items())
        }
    else:
        members = Member.objects.filter(
            email=form.cleaned_data['address'])[:1]
        if settings.HTML_MAILOUT_ENABLED and form.cleaned_data['send_html']:
            body_html = form.cleaned_data['body_html']
        else:
            body_html = None
        if members.count() == 0:
            response = {
                'status': 'error',
                'errors': 'No member found with given email address',
            }
        else:
            error, _, error_message = toolkit.members.tasks.send_mailout_to(
                form.cleaned_data['subject'],
                form.cleaned_data['body_text'],
                body_html,
                members)
            response = {
                'status': 'ok' if not error else 'error',
                'errors': error_message,
            }

    response = HttpResponse(
        json.dumps(response),
        content_type="application/json"
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
    task_id = request.GET["task_id"]

    try:
        async_result = celery.result.AsyncResult(id=task_id)
        state = async_result.state
    except redis.exceptions.ConnectionError as ce:
        logger.error(
            "Failed connecting to redis to retrieve job status: %s", ce
        )
        complete = True
        state = None
        error = True
        sent_count = 0
        error_msg = (
            "Failed connecting to redis to retrieve job status: %s" % ce
        )

    if state:
        progress_parts = state.split("PROGRESS")
        if len(progress_parts) > 1:
            try:
                progress = int(progress_parts[1])
            except ValueError:
                logger.error("Invalid progress from async mailout task: {0}"
                             .format(state))
        elif state == "SUCCESS":
            progress = 100
            complete = True
            if (
                async_result.result
                and isinstance(async_result.result, (tuple, list))
                and len(async_result.result) == 3
            ):
                error, sent_count, error_msg = async_result.result
            else:
                logger.error(
                    "Couldn't retrieve status from completed celery job: %s",
                    str(async_result.result),
                )
                error = True
                sent_count = 0
                error_msg = u"Couldn't retrieve status from completed job"
        elif state == "FAILURE":
            complete = True
            error = True
            if async_result.result:
                error_msg = six.text_type(async_result.result)
            else:
                error_msg = "Failed: Unknown error"
        elif state == "PENDING":
            progress = 0
        else:
            logger.error(u"Invalid data from async mailout task: {0}"
                         .format(state))

    return HttpResponse(
        json.dumps(
            {
                "task_id": task_id,
                "complete": complete,
                "progress": progress,
                "error": error,
                "error_msg": error_msg,
                "sent_count": sent_count,
            }
        ),
        content_type="application/json",
    )
