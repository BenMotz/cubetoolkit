import smtplib
import email.errors

from django.core.mail import (get_connection, EmailMessage,
                              EmailMultiAlternatives)
from django.conf import settings
from django.urls import reverse
import django.template

from celery import task, current_task
from celery.utils.log import get_task_logger

from toolkit.members.models import Member

logger = get_task_logger(__name__)


def _send_email(email_conn, destination, subject, body_text, body_html):
    error = None

    msg_class = EmailMultiAlternatives if body_html else EmailMessage

    msg = msg_class(
        subject=subject,
        body=body_text,
        from_email=settings.VENUE['mailout_from_address'],
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


def send_mailout_report(email_conn, report_to, sent, err_list,
                        subject, body_text, body_html):
        # All done? Send report:
        report_text = ("%d copies of the following were sent out on %s members"
                       " list\n" % (sent, settings.VENUE['name']))
        if len(err_list) > 0:
            # Only send a max of 100 error messages!
            report_text += "{0} errors:\n{1}".format(
                len(err_list), "\n".join(err_list[:100]))
            if len(err_list) > 100:
                report_text += "(Error list truncated at 100 entries)\n"

        report_text += "\n"
        report_text += body_text

        _send_email(email_conn, report_to, subject, report_text, None)


def _get_text_preamble_signature(recipient):
    preamble_template = u"Dear {0},\n\n"
    if False:  # not(recipient.gdpr_opt_in):
        gdpr_opt_in_template = (
            u"If you'd like to continue to receive emails about events and fundraising for the Cube, "
            u"you'll need to make sure you opt-in before 25 May 2018.\n\n"
            u"Please choose to opt-in so you won't miss out on what's happening at your favourite Microplex.\n\n"
            u"Use this link to opt-in:\n\n"
            u"{1}{2}?k={3}\n\n"
        )
    else:
        # gdpr_opt_in_template = u"Congratulations, you opted in on {0}\n\n"
        gdpr_opt_in_template = u""
    signature_template = (
        u"\n"
        u"\n"
        u"If you no longer wish to receive emails from us, please use this "
        u"link:\n"
        u"{0}{1}?k={4}\n"
        u"To see what details we hold on you and to edit the details of "
        u"your membership, please use this link:\n"
        u"{0}{2}?k={4}\n"
        u"To permanently remove your membership details from our records, "
        u"please use this link:\n"
        u"{0}{3}?k={4}\n"
    )
    return (
        preamble_template.format(recipient.name),
        gdpr_opt_in_template.format(
            recipient.gdpr_opt_in,
            settings.VENUE['email_unsubscribe_host'],
            reverse("opt_in", args=(recipient.pk,)),
            recipient.mailout_key,
        ),
        signature_template.format(
            settings.VENUE['email_unsubscribe_host'],
            reverse("unsubscribe-member", args=(recipient.pk,)),
            reverse("edit-member", args=(recipient.pk,)),
            reverse("delete-member", args=(recipient.pk,)),
            recipient.mailout_key,
        ),
    )


def send_mailout_to(subject, body_text, body_html, recipients, task=None,
                    report_to=None):
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

    logger.info("Sending mailout to {0} recipients".format(count))

    html_mail_template = django.template.loader.get_template(
        "mailout_wrapper.html")
    html_mail_context = {
        'subject': subject,
        'body': body_html,
        'email_unsubscribe_host': settings.VENUE['email_unsubscribe_host'],
        'member_name': "member",
        'unsubscribe_link': "[error]",
        'edit_link': "[error]",
        'delete_link': "[error]",
        'mailout_key': "",
    }

    # Open connection to SMTP server:
    email_conn = get_connection(fail_silently=False)
    try:
        email_conn.open()
    except Exception as exc:
        msg = "Failed to connect to SMTP server: {0}".format(exc)
        logger.error(msg)
        return (True, 0, msg)

    err_list = []

    # Uncomment the following line if you want to disable mailout for testing
    # return (True, 0, 'DISABLED UNTIL READY')

    try:
        for recipient in recipients:
            # Build per-recipient signature, with customised unsubscribe links:
            text_pre, text_gdpr, text_post = _get_text_preamble_signature(recipient)

            # Build final email, still in unicode:
            mail_body_text = text_pre + text_gdpr + body_text + text_post

            if body_html:
                html_mail_context.update({
                    'member_name': recipient.name,
                    'unsubscribe_link': reverse("unsubscribe-member",
                                                args=(recipient.pk,)),
                    'edit_link': reverse("edit-member", args=(recipient.pk,)),
                    'delete_link': reverse("delete-member", args=(recipient.pk,)),
                    'mailout_key': recipient.mailout_key
                })
                mail_body_html = html_mail_template.render(html_mail_context)
            else:
                mail_body_html = None

            error = _send_email(email_conn, recipient.email, subject,
                                mail_body_text, mail_body_html)
            if error:
                err_list.append(error)

            sent += 1
            if task and sent % one_percent == 0:
                progress = int((100.0 * sent) / count) + 1
                task.update_state(
                    state='PROGRESS{0:03}'.format(progress),
                    meta={'sent': sent, 'total': count})

        if report_to:
            send_mailout_report(email_conn, report_to, sent, err_list,
                                subject, body_text, body_html)

    except Exception as exc:
        logger.exception("Mailout job failed, '{0}'".format(exc))
        return (True, sent, "Mailout job died: '{0}'".format(exc))
    finally:
        try:
            email_conn.close()
        except smtplib.SMTPException as smtpe:
            logger.error("SMTP Quit failed: {0}".format(smtpe))

    return (False, sent, 'Ok')


@task()
def send_mailout(subject, body_text, body_html):
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
        logger.error("No recipients found")
        return (True, 0, 'No recipients found')

    return send_mailout_to(
        subject, body_text, body_html, recipients, task=current_task,
        report_to=settings.VENUE['mailout_delivery_report_to'])
