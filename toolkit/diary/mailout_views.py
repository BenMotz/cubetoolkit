import datetime
import logging

from django.urls import reverse

from django.http import HttpResponseRedirect
from django.shortcuts import render
import django.template
import django.db
import django.utils.timezone as timezone
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)
from django.conf import settings

from toolkit.diary.models import Showing
from toolkit.members.models import Member
import toolkit.mailer.forms as mailer_forms
import toolkit.diary.forms as diary_forms
from toolkit.mailer.models import MailoutJob

# Shared utility method:

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _render_mailout_subject_and_body(days_ahead, copy_days_ahead):
    # Render default mail contents. Returns (subject, text mail, html mail)

    # Read data
    start_date = timezone.now()
    end_date = start_date + datetime.timedelta(days=days_ahead)
    copy_end_date = start_date + datetime.timedelta(days=copy_days_ahead)
    showings = (
        Showing.objects.public()
        .not_cancelled()
        .start_in_range(start_date, end_date)
        .order_by("start")
        .select_related()
        .prefetch_related("event__showings")
    )

    event_ids = set()
    showings_once_per_event = []
    show_cheap_night_key = False
    for s in showings.public().start_in_range(start_date, copy_end_date):
        if s.sold_out:
            continue
        if s.event_id not in event_ids:
            showings_once_per_event.append(s)
            event_ids.add(s.event_id)
        show_cheap_night_key = show_cheap_night_key or s.discounted

    try:
        # %-d strips the leading 0 from the day of the month - as per the
        # python docs, this is platform specific to Linux / glibc. See
        # strftime(3).
        first_event_date = showings[0].start.strftime(" commencing %A %-d %B")
    except IndexError:  # Corner case for no events
        first_event_date = ""
    subject_text = "%s forthcoming events%s" % (
        settings.VENUE["longname"],
        first_event_date,
    )

    # Render into mail templates
    text_mail_template = django.template.loader.get_template(
        "mailout_body.txt"
    )

    html_mail_template = django.template.loader.get_template(
        "mailout_body.html"
    )

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "showings": showings,
        "showings_details": showings_once_per_event,
        "copy_days_ahead": copy_days_ahead,
        "show_cheap_night_key": show_cheap_night_key,
        "site_url": settings.VENUE["url"],
    }

    return (
        subject_text,
        text_mail_template.render(context),
        html_mail_template.render(context),
    )


def _render_mailout_form(request, body_text, body_html, subject_text, context):
    form = diary_forms.MailoutForm(
        html_mailout_enabled=settings.HTML_MAILOUT_ENABLED,
        initial={
            "subject": subject_text,
            "body_text": body_text,
            "body_html": body_html,
        },
    )
    context["form"] = form
    return render(request, "form_mailout.html", context)


@permission_required("toolkit.write")
@require_http_methods(["GET", "POST"])
def mailout(request):
    # This view loads a form with a draft mailout subject & body. When the user
    # is happy, they click "Send", which POSTs the data back to this view. If
    # the data pases the basic checks then it gets sent back in the
    # "mailout_send" form. That form has javascript which, if the user
    # confirms, posts to the "exec-mailout" view

    if request.method == "GET":
        days_ahead = settings.MAILOUT_LISTINGS_DAYS_AHEAD
        copy_days_ahead = settings.MAILOUT_DETAILS_DAYS_AHEAD

        try:
            days_ahead = int(request.GET.get("daysahead", days_ahead))
            copy_days_ahead = int(
                request.GET.get("copydaysahead", copy_days_ahead)
            )
        except ValueError:
            pass
        subject_text, body_text, body_html = _render_mailout_subject_and_body(
            days_ahead, copy_days_ahead
        )
        context = {
            "days_ahead": days_ahead,
            "copy_days_ahead": copy_days_ahead,
        }
        return _render_mailout_form(
            request, body_text, body_html, subject_text, context
        )
    elif request.method == "POST":
        form = diary_forms.MailoutForm(
            request.POST, html_mailout_enabled=settings.HTML_MAILOUT_ENABLED
        )
        if not form.is_valid():
            return render(request, "form_mailout.html", {"form": form})

        job_data = request.POST.copy()
        job_data["send_at"] = timezone.now() + datetime.timedelta(minutes=5)

        return render(request, "mailout_send.html", context = {
            "form": mailer_forms.JobForm(job_data),
            "email_count": Member.objects.mailout_recipients().count(),
        })


@permission_required("toolkit.write")
@require_POST
def queue_mailout(request):
    # If we have a query parameter "send_at=now" then we'll fiddle the send_at
    # from the form data to be right now:
    send_right_now = request.GET.get("send_at") == "now"

    form_data = request.POST.copy()
    if send_right_now:
        form_data["send_at"] = timezone.now() + datetime.timedelta(seconds=2)

    form = mailer_forms.JobForm(form_data)
    if not form.is_valid():
        logger.error(f"Create mailout job failed: {repr(form.errors)}")
        return render(request, "mailout_send.html", context = {
            "form": form,
            "email_count": Member.objects.mailout_recipients().count(),
        })
    logger.info(
        f"Queueing mailout job, send_at: {form.cleaned_data['send_at']}, subject: {form.cleaned_data['subject']}"
    )
    form.save()
    return HttpResponseRedirect(reverse("mailer:jobs-list"))
