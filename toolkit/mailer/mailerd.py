import logging
import time
import smtplib
import email.errors
from typing import List, Tuple

from django.core.mail import (
    get_connection,
    EmailMessage,
    EmailMultiAlternatives,
)
from django.conf import settings
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
import django.template

from toolkit.members.models import Member
from .models import MailoutJob

logger = logging.getLogger(__name__)

POLL_PERIOD_S = 1


def _send_email(email_conn, destination, subject, body_text, body_html):
    error = None

    msg_class = EmailMultiAlternatives if body_html else EmailMessage

    msg = msg_class(
        subject=subject,
        body=body_text,
        from_email=settings.VENUE["mailout_from_address"],
        to=[destination],
        connection=email_conn,
    )

    if body_html:
        msg.attach_alternative(body_html, "text/html")

    try:
        msg.send()
    except email.errors.MessageParseError as hpe:
        error = "Failed sending to '{0}': {1}".format(destination, hpe)
        logger.error(error)
    except smtplib.SMTPServerDisconnected as ssd:
        logger.error("Failed sending to '{0}': {1}".format(destination, ssd))
        # don't handle this:
        raise
    except smtplib.SMTPException as smtpe:
        error = str(smtpe)
        logger.error("Failed sending to '{0}': {1}".format(destination, smtpe))

    return error


def send_mailout_report(
    email_conn, report_to, sent, err_list, subject, body_text
):
    # All done? Send report:
    report_text = (
        "%d copies of the following were sent out on %s members"
        " list\n" % (sent, settings.VENUE["name"])
    )
    if len(err_list) > 0:
        # Only send a max of 100 error messages!
        report_text += "{0} errors:\n{1}".format(
            len(err_list), "\n".join(err_list[:100])
        )
        if len(err_list) > 100:
            report_text += "(Error list truncated at 100 entries)\n"

    report_text += "\n"
    report_text += body_text

    _send_email(email_conn, report_to, subject, report_text, None)


def _get_text_preamble_signature(recipient) -> Tuple[str, str]:
    preamble_template = "Dear {0},\n\n"
    signature_template = (
        "\n"
        "\n"
        "If you no longer wish to receive emails from us, please use this "
        "link:\n"
        "{0}{1}?k={4}\n"
        "To see what details we hold on you and to edit the details of "
        "your membership, please use this link:\n"
        "{0}{2}?k={4}\n"
        "To permanently remove your membership details from our records, "
        "please use this link:\n"
        "{0}{3}?k={4}\n"
    )
    return (
        preamble_template.format(recipient.name),
        signature_template.format(
            settings.VENUE["email_unsubscribe_host"],
            reverse("unsubscribe-member", args=(recipient.pk,)),
            reverse("edit-member", args=(recipient.pk,)),
            reverse("delete-member", args=(recipient.pk,)),
            recipient.mailout_key,
        ),
    )


def send_mailout_to(
    job: MailoutJob,
    recipients: QuerySet[Member],
    report_to=None,
):
    """
    Sends email with supplied subject/body to supplied set of recipients.
    Requires subject and body to be unicode.

    returns a tuple:
    (error, sent_count, error_message)
    where error is True if an error occurred.
    """

    count = recipients.count()
    sent = 0
    one_percent = count // 100 or 1
    start_time = time.monotonic()

    logger.info("Sending mailout to {0} recipients".format(count))

    html_mail_template = django.template.loader.get_template(
        "mailout_wrapper.html"
    )
    html_mail_context = {
        "subject": job.subject,
        "body": job.body_html,
        "email_unsubscribe_host": settings.VENUE["email_unsubscribe_host"],
        "member_name": "member",
        "unsubscribe_link": "[error]",
        "edit_link": "[error]",
        "delete_link": "[error]",
        "mailout_key": "",
    }

    # Open connection to SMTP server:
    email_conn = get_connection(fail_silently=False)
    try:
        email_conn.open()
    except Exception as exc:
        msg = "Failed to connect to SMTP server: {0}".format(exc)
        logger.error(msg)
        job.do_fail(msg)
        job.save()
        return

    err_list = []

    try:
        for recipient in recipients:
            if sent % one_percent == 0 or (
                time.monotonic() - start_time > POLL_PERIOD_S
            ):
                job.refresh_from_db()
                if job.keep_sending():
                    job.do_sending(sent, count)
                    job.save()

            if not job.keep_sending():
                logger.info(f"Aborting job: {job}")
                break

            # Build per-recipient signature, with customised unsubscribe links:
            text_pre, text_post = _get_text_preamble_signature(recipient)

            # Build final email, still in unicode:
            mail_body_text = text_pre + job.body_text + text_post

            if job.body_html:
                html_mail_context.update(
                    {
                        "member_name": recipient.name,
                        "unsubscribe_link": reverse(
                            "unsubscribe-member", args=(recipient.pk,)
                        ),
                        "edit_link": reverse(
                            "edit-member", args=(recipient.pk,)
                        ),
                        "delete_link": reverse(
                            "delete-member", args=(recipient.pk,)
                        ),
                        "mailout_key": recipient.mailout_key,
                    }
                )
                mail_body_html = html_mail_template.render(html_mail_context)
            else:
                mail_body_html = None

            error = _send_email(
                email_conn,
                recipient.email,
                job.subject,
                mail_body_text,
                mail_body_html,
            )
            if error:
                err_list.append(error)

            sent += 1

        job.do_complete(sent=sent)
        job.save()

        if report_to:
            send_mailout_report(
                email_conn,
                report_to,
                sent,
                err_list,
                job.subject,
                job.body_text,
            )

    except Exception as exc:
        logger.exception(f"Mailout job failed, '{exc}")
        job.do_fail(f"Mailout job died: '{exc}'")
        job.save()
    finally:
        try:
            email_conn.close()
        except smtplib.SMTPException as smtpe:
            logger.error(f"SMTP Quit failed: {smtpe}")

    logger.info("Mailout complete")


def run_job(job: MailoutJob) -> None:
    """
    Sends email with supplied subject/body to all members who have an email
    address, and who have mailout==True and mailout_failed=False.

    Requires subject and body to be unicode.

    Also sends an email to settings.VENUE['mailout_delivery_report_to'] when
    done.

    returns a tuple:
    (error, sent_count, error_message)
    where error is True if an error occurred.
    """

    recipients = Member.objects.mailout_recipients()
    count = recipients.count()

    if count == 0:
        job.do_fail("No recipients found")
        job.save()
        return

    job.do_sending(sent=0, total=count)
    job.save()

    send_mailout_to(
        job,
        recipients,
        report_to=settings.VENUE["mailout_delivery_report_to"],
    )


def poll_for_pending() -> List[MailoutJob]:
    return list(
        MailoutJob.objects.filter(state=MailoutJob.SendState.PENDING)
        .filter(send_at__lte=timezone.now())
        .order_by("created_at")
    )


def clean_up():
    interrupted_jobs = MailoutJob.objects.filter(
        state=MailoutJob.SendState.SENDING
    )
    for job in interrupted_jobs:
        logger.info(f"Will not resume interrupted job: {job}")
        job.do_fail("Mailerd restarted while job was in progress")
        job.save()

    half_cancelled_jobs = MailoutJob.objects.filter(
        state=MailoutJob.SendState.CANCELLING
    )
    for job in half_cancelled_jobs:
        logger.info(f"Cancelled: {job}")
        job.do_complete_cancel()
        job.save()


def run() -> None:
    logger.info("Starting mailerd")
    clean_up()
    while True:
        time.sleep(POLL_PERIOD_S)
        pending_jobs = poll_for_pending()
        for idx, job in enumerate(pending_jobs):
            logger.info(f"Running job {idx+1}/{len(pending_jobs)}: {job}")
            run_job(job)
