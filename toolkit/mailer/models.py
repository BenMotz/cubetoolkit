import logging
from django.db import models

from toolkit.diary.validators import validate_in_future

logger = logging.getLogger(__name__)


class FutureDateTimeField(models.DateTimeField):
    """DateTime field that can only be set to times in the future."""

    default_error_messages = {
        "invalid": "Date may not be in the past",
    }
    default_validators = [validate_in_future]


class MailoutStateError(Exception):
    pass


class MailoutJob(models.Model):
    class SendState(models.TextChoices):
        # Initial state:
        PENDING = "PENDING", "Pending"
        # Thence:
        SENDING = "SENDING", "Sending"
        # And
        CANCELLING = "CANCELLING", "Cancelling"
        # Terminal states:
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

        # i.e. States;
        # PENDING ---> SENDING ---> SENT
        #         |            \--> FAILED
        #         |            \--> CANCELLING ---> CANCELLED
        #         |                            \--> FAILED
        #         \--> CANCELLED

    send_at = FutureDateTimeField(db_index=True)
    state = models.CharField(
        max_length=10, choices=SendState.choices, default=SendState.PENDING
    )
    status = models.CharField(
        blank=False, max_length=255, default="Waiting to start"
    )
    progress_pct = models.SmallIntegerField(default=0)
    send_count = models.IntegerField(default=0)

    send_html = models.BooleanField()
    subject = models.TextField()
    body_text = models.TextField()
    body_html = models.TextField()
    recipient_filter = models.CharField(blank=True, max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    TERMINAL = {SendState.SENT, SendState.FAILED, SendState.CANCELLED}

    def cancellable(self) -> bool:
        return self.state in (
            MailoutJob.SendState.PENDING,
            MailoutJob.SendState.SENDING,
        )

    def keep_sending(self) -> bool:
        return self.state == MailoutJob.SendState.SENDING

    def do_sending(self, sent: int, total: int) -> bool:
        progress_pct = int((100.0 * sent) / total) + 1
        if self.state not in (
            MailoutJob.SendState.PENDING,
            MailoutJob.SendState.SENDING,
        ):
            self.do_fail(
                f"Inconsistent state, tried to send while '{self.state}'"
            )
            return False
        self.state = MailoutJob.SendState.SENDING
        self.status = "Sending"
        self.progress_pct = progress_pct
        self.send_count = total
        return True

    def do_cancel(self) -> None:
        if self.state == MailoutJob.SendState.PENDING:
            self.state = MailoutJob.SendState.CANCELLED
        elif self.state == MailoutJob.SendState.SENDING:
            self.state = MailoutJob.SendState.CANCELLING
        elif self.state in (
            MailoutJob.SendState.CANCELLED,
            MailoutJob.SendState.CANCELLING,
        ):
            pass
        else:
            raise MailoutStateError(f"Cannot cancel in state {self.state}")
        self.status = "cancelled"

    def do_complete_cancel(self) -> None:
        if self.state == MailoutJob.SendState.CANCELLING:
            self.state = MailoutJob.SendState.CANCELLED

    def do_fail(self, status: str) -> None:
        if self.state in self.TERMINAL:
            logger.error(f"Tried to fail from terminal state: {self}")
            return
        logger.info(f"Mailout job failed, '{status}': {self}")
        self.status = status
        self.state = MailoutJob.SendState.FAILED

    def do_complete(self, sent: int) -> None:
        self.send_count = sent
        if self.state in self.TERMINAL:
            logger.error(f"Tried to complete from terminal state: {self}")
        elif self.state == MailoutJob.SendState.PENDING:
            logger.error(f"Tried to complete from pending state: {self}")
            self.state = MailoutJob.SendState.FAILED
            self.status = "Inconsistent state, completed while pending"
        elif self.state == MailoutJob.SendState.SENDING:
            self.state = MailoutJob.SendState.SENT
            self.status = "Complete"
            self.progress_pct = 100
        elif self.state == MailoutJob.SendState.CANCELLING:
            self.state = MailoutJob.SendState.CANCELLED
            self.status = "Cancelled"

    def __str__(self) -> str:
        return (
            f"Job id={self.pk} state={self.state} progress_pct={self.progress_pct} "
            f"send_at={self.send_at} created_at={self.created_at} updated_at={self.updated_at}"
        )
