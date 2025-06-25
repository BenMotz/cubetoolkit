import logging
import time
import smtplib
import email.errors
from typing import List, Optional, Tuple

from django.core.mail import (
    get_connection,
    EmailMessage,
    EmailMultiAlternatives,
)
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.db.models import QuerySet
from django.urls import reverse
import django.template

from toolkit.members.models import Member
from .models import MailoutJob

logger = logging.getLogger(__name__)

POLL_FOR_CANCEL_PERIOD_S = 1


def _send_email(
    email_conn: BaseEmailBackend,
    destination: str,
    subject: str,
    body_text: str,
    body_html: Optional[str],
) -> Optional[str]:
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
        error = f"Failed sending to '{destination}': {hpe}"
        logger.error(error)
    except smtplib.SMTPServerDisconnected as ssd:
        logger.error(f"Failed sending to '{destination}': {ssd}")
        # don't handle this:
        raise
    except smtplib.SMTPException as smtpe:
        error = str(smtpe)
        logger.error(f"Failed sending to '{destination}': {smtpe}")

    return error


def send_mailout_report(
    email_conn: BaseEmailBackend,
    report_to: str,
    sent: int,
    err_list: List[str],
    subject: str,
    body_text: str,
) -> None:
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


def _get_text_preamble_signature(recipient: Member) -> Tuple[str, str]:
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
) -> None:
    """
    Sends email with supplied subject/body to supplied set of recipients.
    Requires subject and body to be unicode.
    """

    count = recipients.count()
    sent = 0
    one_percent = count // 100 or 1
    start_time = time.monotonic()

    logger.info(f"Sending mailout to {count} recipients")

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
        msg = f"Failed to connect to SMTP server: {exc}"
        logger.error(msg)
        job.do_fail(msg)
        job.save()
        return

    err_list = []

    try:
        for recipient in recipients:
            if sent % one_percent == 0 or (
                time.monotonic() - start_time > POLL_FOR_CANCEL_PERIOD_S
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

            if job.send_html and job.body_html:
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
