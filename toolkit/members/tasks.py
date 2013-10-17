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


def _send_email(smtp_conn, destination, subject, body, mail_is_ascii):
    error = None

    # Body, encoded in either ASCII or UTF-8:
    body_charset = "ascii" if mail_is_ascii else "utf-8"
    msg = MIMEText(body.encode(body_charset, "replace"), "plain", body_charset)

    # Assume 'From' is always ASCII(!)
    msg['From'] = settings.MAILOUT_FROM_ADDRESS
    # This will try encoding in ascii, then iso-8859-1 then fallback to UTF-8
    # if that fails. (This is desirable as iso-8859-1 is more readable without
    # decoding, plus more compact)
    # ('To' can contain non-ascii in name part, i.e. "name <address>")
    msg['To'] = Header(destination, "iso-8859-1")
    msg['Subject'] = Header(subject, "iso-8859-1")

    try:
        # Enforce ascii destination email address:
        smtp_conn.sendmail(settings.MAILOUT_FROM_ADDRESS,
                           [destination.encode("ascii")],
                           msg.as_string())
    except UnicodeError:
        msg = "Non-ascii email address {0}".format(destination.encode("ascii", "replace"))
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


@task()
def send_mailout(subject, body):
    """
    Sends email with supplied subject/body to all members who have an email
    address, and who have mailout==True and mailout_failed=False.

    Requires subject and body to be unicode.

    Also sends an email to settings.MAILOUT_DELIVERY_REPORT_TO when done.

    returns a tuple:
    (error, sent_count, error_message)
    where error is True if an error occurred.
    """

    header_template = u"Dear {0},\n\n"
    signature_template = (
        u"\n" +
        u"\n" +
        u"If you wish to be removed from our mailing list please use this link:\n" +
        u"http://{0}{{0}}?k={{2}}\n" +
        u"To edit details of your membership, please use this link:\n" +
        u"http://{0}{{1}}?k={{2}}\n"
    ).format(settings.EMAIL_UNSUBSCRIBE_HOST)

    recipients = Member.objects.mailout_recipients()
    count = recipients.count()
    sent = 0
    one_percent = count // 100 or 1

    if count == 0:
        logger.error("No recipients found")
        return (True, 0, 'No recipients found')

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
    body_is_ascii = string_is_ascii(body) and string_is_ascii(signature_template)

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
            mail_body = header + body + signature
            mail_is_ascii = body_is_ascii and string_is_ascii(header)

            error = _send_email(smtp_conn, recipient.email, subject, mail_body, mail_is_ascii)

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

        _send_email(smtp_conn, unicode(settings.MAILOUT_DELIVERY_REPORT_TO), subject, report, body_is_ascii)

    except Exception as exc:
        logger.exception("Mailout job failed, {0}".format(exc))
        return (True, sent, "Mailout job died: {0}".format(exc))
    finally:
        try:
            smtp_conn.quit()
        except smtplib.SMTPException as smtpe:
            logger.error("SMTP Quit failed: {0}".format(smtpe))

    return (False, sent, 'Ok')
