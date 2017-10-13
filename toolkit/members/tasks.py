import smtplib
from email import charset
from email.mime.text import MIMEText
from email.header import Header

import six
from django.conf import settings
from django.core.urlresolvers import reverse

from celery import task, current_task
from celery.utils.log import get_task_logger

from toolkit.members.models import Member

logger = get_task_logger(__name__)


def string_is_ascii(string):
    return all(ord(char) < 0x7F for char in string)


def _send_email(smtp_conn, destination, subject, body, mail_is_ascii):
    error = None

    # Body, encoded in either ASCII or UTF-8:
    body_charset = "ascii" if mail_is_ascii else "utf-8"
    msg = MIMEText(body.encode(body_charset, "replace"), "plain", body_charset)

    # Assume 'From' is always ASCII(!)
    msg['From'] = settings.VENUE['mailout_from_address']
    msg['To'] = Header(destination)
    msg['Subject'] = Header(subject)

    try:
        # Enforce ascii destination email address:
        if six.PY2:
            smtp_conn.sendmail(settings.VENUE['mailout_from_address'],
                               [destination.encode("ascii")],
                               msg.as_string())
        else:
            smtp_conn.sendmail(settings.VENUE['mailout_from_address'],
                               [destination],
                               msg.as_string().encode("utf-8"))

    except UnicodeError:
        msg = "Non-ascii email address {0}".format(
            destination.encode("ascii", "replace"))
        logger.error(msg)
        return msg
    except smtplib.SMTPServerDisconnected as ssd:
        logger.error("Failed sending to {0}: {1}".format(destination, ssd))
        # don't handle this:
        raise
    except smtplib.SMTPException as smtpe:
        error = str(smtpe)
        logger.error("Failed sending to {0}: {1}".format(destination, smtpe))

    return error


def send_mailout_report(smtp_conn, report_to, sent, err_list,
        subject, body, body_is_ascii):
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

        _send_email(smtp_conn, report_to,
                    subject, report, body_is_ascii)


def send_mailout_to(subject, body, recipients, task=None, report_to=None):
    """
    Sends email with supplied subject/body to supplied set of recipients.
    Requires subject and body to be unicode.

    returns a tuple:
    (error, sent_count, error_message)
    where error is True if an error occurred.
    """

    # Configure to 'intelligently' use shortest encoding for subject, but just
    # send body of email as 8 bit plain. (This was the default behaviour in
    # Django 1.5.x - retain it so as not to rock the boat for mail delivery)
    charset.add_charset('utf-8', charset.SHORTEST, None, 'utf-8')

    header_template = u"Dear {0},\n\n"
    signature_template = (
        u"\n"
        u"\n"
        u"If you wish to be removed from our mailing list please use this "
        u"link:\n"
        u"http://{0}{{0}}?k={{2}}\n"
        u"To edit details of your membership, please use this link:\n"
        u"http://{0}{{1}}?k={{2}}\n"
    ).format(settings.VENUE['email_unsubscribe_host'])

    count = recipients.count()
    sent = 0
    one_percent = count // 100 or 1

    logger.info("Sending mailout to {0} recipients".format(count))

    # Open connection to SMTP server:
    try:
        smtp_conn = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    except Exception as exc:
        msg = "Failed to connect to SMTP server: {0}".format(exc)
        logger.error(msg)
        return (True, 0, msg)

    # Cache if body is 7 bit clean (will need to check each sender name, but
    # save a bit of time by not scanning everything)
    body_is_ascii = (
        string_is_ascii(body) and
        string_is_ascii(signature_template))

    err_list = []

    # Uncomment the following line if you want to disable mailout for testing
    # return (True, 0, 'DISABLED UNTIL READY')

    try:
        for recipient in recipients:
            # Nb; this is not the email header, it's just the "Dear XYZ"
            # bit at the top of the mail:
            header = header_template.format(
                recipient.name
            )

            # Build per-recipient signature, with customised unsubscribe links:
            signature = signature_template.format(
                reverse("unsubscribe-member", args=(recipient.pk,)),
                reverse("edit-member", args=(recipient.pk,)),
                recipient.mailout_key,
            )
            # Build final email, still in unicode:
            mail_body = header + body + signature
            mail_is_ascii = body_is_ascii and string_is_ascii(header)

            error = _send_email(smtp_conn, recipient.email,
                                subject, mail_body, mail_is_ascii)

            if error:
                err_list.append(error)

            sent += 1
            if task and sent % one_percent == 0:
                progress = int((100.0 * sent) / count) + 1
                task.update_state(
                    state='PROGRESS{0:03}'.format(progress),
                    meta={'sent': sent, 'total': count})

        if report_to:
            send_mailout_report(smtp_conn, report_to, sent, err_list,
                subject, body, body_is_ascii)

    except Exception as exc:
        logger.exception("Mailout job failed, '{0}'".format(exc))
        return (True, sent, "Mailout job died: '{0}'".format(exc))
    finally:
        try:
            smtp_conn.quit()
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

    return send_mailout_to(subject, body, recipients, task=current_task,
        report_to=settings.VENUE['mailout_delivery_report_to'])
