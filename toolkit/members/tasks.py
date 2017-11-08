import smtplib

import django.core.mail
from django.conf import settings
from django.urls import reverse

from celery import task, current_task
from celery.utils.log import get_task_logger

from toolkit.members.models import Member

logger = get_task_logger(__name__)


def _send_email(email_conn, destination, subject, body):
    error = None

    msg = django.core.mail.EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.VENUE['mailout_from_address'],
        to=[destination],
        connection=email_conn,
    )

    try:
        msg.send()
    except smtplib.SMTPServerDisconnected as ssd:
        logger.error("Failed sending to {0}: {1}".format(destination, ssd))
        # don't handle this:
        raise
    except smtplib.SMTPException as smtpe:
        error = str(smtpe)
        logger.error("Failed sending to {0}: {1}".format(destination, smtpe))

    return error


def send_mailout_report(email_conn, report_to, sent, err_list,
                        subject, body):
        # All done? Send report:
        report = ("%d copies of the following were sent out on %s members "
                  "list\n" % (sent, settings.VENUE['name']))
        if len(err_list) > 0:
            # Only send a max of 100 error messages!
            report += "{0} errors:\n{1}".format(
                len(err_list), "\n".join(err_list[:100]))
            if len(err_list) > 100:
                report += "(Error list truncated at 100 entries)\n"

        report += "\n"
        report += body

        _send_email(email_conn, report_to, subject, report)


def send_mailout_to(subject, body, recipients, task=None, report_to=None):
    """
    Sends email with supplied subject/body to supplied set of recipients.
    Requires subject and body to be unicode.

    returns a tuple:
    (error, sent_count, error_message)
    where error is True if an error occurred.
    """

    preamble_template = u"Dear {0},\n\n"
    signature_template = (
        u"\n"
        u"\n"
        u"If you wish to be removed from our mailing list please use this "
        u"link:\n"
        u"{0}{{0}}?k={{2}}\n"
        u"To edit details of your membership, please use this link:\n"
        u"{0}{{1}}?k={{2}}\n"
    ).format(settings.VENUE['email_unsubscribe_host'])

    count = recipients.count()
    sent = 0
    one_percent = count // 100 or 1

    logger.info("Sending mailout to {0} recipients".format(count))

    # Open connection to SMTP server:
    email_conn = django.core.mail.get_connection(fail_silently=False)
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
            body_preamble = preamble_template.format(recipient.name)

            # Build per-recipient signature, with customised unsubscribe links:
            signature = signature_template.format(
                reverse("unsubscribe-member", args=(recipient.pk,)),
                reverse("edit-member", args=(recipient.pk,)),
                recipient.mailout_key,
            )
            # Build final email, still in unicode:
            mail_body = body_preamble + body + signature

            error = _send_email(email_conn, recipient.email, subject,
                                mail_body)
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
                                subject, body)

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
def send_mailout(subject, body):
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
        subject, body, recipients, task=current_task,
        report_to=settings.VENUE['mailout_delivery_report_to'])
