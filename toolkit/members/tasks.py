import smtplib
from email.mime.text import MIMEText
from email.Header import Header

from django.conf import settings
from django.core.urlresolvers import reverse

from celery import task, current_task
from celery.utils.log import get_task_logger

from toolkit.members.models import Member

logger = get_task_logger(__name__)


def string_is_ascii(string):
    return all(ord(char) < 0x7F for char in string)


def get_ascii_or_encoded_header(string):
    if string_is_ascii(string):
        return string.encode("ascii")
    else:
        return Header(string.encode("utf-8"), "utf-8")


def _send_email(smtp_conn, destination, subject, body):
    error = None

    msg = MIMEText(body.encode("utf-7"))
    # Change the message encoding to match:
    msg.set_charset("utf-7")

    # Assume 'From' is always ASCII(!)
    msg['From'] = settings.MAILOUT_FROM_ADDRESS
    msg['To'] = get_ascii_or_encoded_header(destination)
    msg['Subject'] = get_ascii_or_encoded_header(subject)

    try:
        smtp_conn.sendmail(settings.MAILOUT_FROM_ADDRESS,
                           [destination],
                           msg.as_string())
    except smtplib.SMTPServerDisconnected as ssd:
        logger.error("Failed sending to {0}: {1}".format(destination, ssd))
        # don't handle this:
        raise
    except smtplib.SMTPException as smtpe:
        error = str(smtpe)
        logger.error("Failed sending to {0}: {1}".format(destination, smtpe))

    return error


@task()
def send_mailout(subject, body):
    """
    Sends email with supplied subject/body to all members who have an email
    address, and who have mailout==True and mailout_failed=False.

    Also sends an email to settings.MAILOUT_DELIVERY_REPORT_TO when done

    returns a tuple:
    (error, sent_count, error_message)
    where error is True if an error occurred
    """

    header_template = u"Dear {0},\n\n"
    signature_template = (
        u"""

If you wish to be removed from our mailing list please use this link:
http://{0}{{0}}?k={{2}}
To edit details of your membership, please use this link:
http://{0}{{1}}?k={{2}}
""").format(settings.EMAIL_UNSUBSCRIBE_HOST, settings.EMAIL_UNSUBSCRIBE_HOST)

    recipients = (Member.objects.filter(email__isnull=False)
                                .exclude(email='')
                                .exclude(mailout_failed=True)
                                .filter(mailout=True))
    count = recipients.count()
    sent = 0
    one_percent = count // 100 or 1

    logger.info("Sending mailout to {0} recipients".format(count))

    if count == 0:
        return (True, 0, 'No recipients found')

    # Open connection to SMTP server:
    try:
        smtp_conn = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    except Exception as exc:
        msg = "Failed to connect to SMTP server: {0}".format(exc)
        logger.error(msg)
        return (True, 0, msg)

    err_list = []

    # XXX XXX XXX
    # DELETE THE FOLLOWING LINE IF YOU WANT TO TRY EMAILING FOR REALSIES
    # XXX XXX XXX
    return (True, 0, 'DISABLED UNTIL READY')

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
            email_body = header + body + signature

            error = _send_email(smtp_conn, recipient.email, subject, email_body)

            if error:
                err_list.append(error)

            sent += 1
            if sent % one_percent == 0:
                progress = int((100.0 * sent) / count) + 1
                current_task.update_state(state='PROGRESS{0:03}'.format(progress),
                                          meta={'sent': sent, 'total': count})
        # All done? Send report:
        report = "{0} copies of the following were sent out on cube members list\n".format(sent)
        if len(err_list) > 0:
            # Only send a max of 100 error messages!
            report += "{0} errors:\n{1}".format(len(err_list), "\n".join(err_list[:100]))
            if len(err_list) > 100:
                report += "(Error list truncated at 100 entries)\n"

        report += "\n"
        report += body

        _send_email(smtp_conn, settings.MAILOUT_DELIVERY_REPORT_TO, subject, report)

    except Exception as exc:
        logger.exception("Mailout job failed, {0}".format(exc))
        return (True, sent, "Mailout job died: {0}".format(exc))
    finally:
        try:
            smtp_conn.quit()
        except smtplib.SMTPException as smtpe:
            logger.error("SMTP Quit failed: {0}".format(smtpe))

    return (False, sent, 'Ok')
