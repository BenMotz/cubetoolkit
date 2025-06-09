import logging
import time
import signal
from typing import List, Optional
from types import FrameType

from django.conf import settings
from django.utils import timezone

from toolkit.members.models import Member
from .models import MailoutJob
from .sender import send_mailout_to

logger = logging.getLogger(__name__)

POLL_PERIOD_S = 5


def run_job(job: MailoutJob) -> None:
    """
    Sends email with supplied subject/body to all members who have an email
    address, and who have mailout==True and mailout_failed=False.

    Requires subject and body to be unicode.

    Also sends an email to settings.VENUE['mailout_delivery_report_to'] when
    done.
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


def clean_up() -> None:
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
    keep_running = True

    def term_handler(signo: int, frame: Optional[FrameType]) -> None:
        nonlocal keep_running
        keep_running = False
        logger.info(f"Received signal {signal.Signals(signo).name}")

    signal.signal(signal.SIGINT, term_handler)
    signal.signal(signal.SIGTERM, term_handler)

    while keep_running:
        time.sleep(POLL_PERIOD_S)
        pending_jobs = poll_for_pending()
        for idx, job in enumerate(pending_jobs):
            logger.info(f"Running job {idx+1}/{len(pending_jobs)}: {job}")
            run_job(job)
