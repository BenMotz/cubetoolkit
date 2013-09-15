from django.conf import settings
from django.core.urlresolvers import reverse

from celery import task, current_task

from toolkit.members.models import Member


@task()
def send_mailout(subject, body):
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
    one_percent = count // 100

    if count == 0:
        return (False, 1000, ['blah', 'blah', 'blah'])

    with open("/tmp/spool", "w") as spool:
        for recipient in recipients:
            header = header_template.format(
                recipient.name
            )

            signature = signature_template.format(
                reverse("edit-member", args=(recipient.pk,)),
                reverse("unsubscribe-member", args=(recipient.pk,)),
                recipient.mailout_key,
            )

            sent += 1
            if sent % one_percent == 0:
                progress = int((100.0 * sent) / count) + 1
                current_task.update_state(state='PROGRESS{0:03}'.format(progress),
                                          meta={'sent': sent, 'total': count})
                # yield "{0}\n".format(progress)
            # Send the frigging mail...
            # bork(body + signature)
            email = header + body + signature
            spool.write(email.encode("utf-8"))
            spool.write("\n~~\n")

    return (True, 1000, ['blah', 'blah', 'blah'])
