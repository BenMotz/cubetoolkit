from unittest.mock import patch
from datetime import timedelta

from django.test import TestCase
from django.conf import settings
import django.utils.timezone as timezone

from ...members.tests.common import MembersTestsMixin
from ...members.models import Member
from ..models import MailoutJob
import toolkit.mailer.mailerd as mailerd


class TestPollForPending(TestCase):
    def test_pending_none(self) -> None:
        self.assertEqual(0, MailoutJob.objects.count())
        pending = mailerd.poll_for_pending()
        self.assertListEqual([], pending)

    def test_pending_in_future(self) -> None:
        MailoutJob.objects.create(
            subject="s",
            body_text="t",
            body_html="h",
            send_html=True,
            send_at=timezone.now() + timedelta(days=1),
        )
        self.assertEqual(1, MailoutJob.objects.count())
        pending = mailerd.poll_for_pending()
        self.assertListEqual([], pending)

    def test_pending_in_past(self) -> None:
        job = MailoutJob.objects.create(
            subject="s",
            body_text="t",
            body_html="h",
            send_html=True,
            send_at=timezone.now() - timedelta(days=1),
        )
        pending = mailerd.poll_for_pending()
        self.assertListEqual([job], pending)

    def test_non_pending_in_past(self) -> None:
        states = [
            MailoutJob.SendState.SENDING,
            MailoutJob.SendState.CANCELLING,
            MailoutJob.SendState.SENT,
            MailoutJob.SendState.FAILED,
            MailoutJob.SendState.CANCELLED,
        ]
        for state in states:
            MailoutJob.objects.create(
                subject="s",
                body_text="t",
                body_html="h",
                send_html=True,
                send_at=timezone.now() - timedelta(days=1),
                state=state,
            )
        pending = mailerd.poll_for_pending()
        self.assertListEqual([], pending)


class TestCleanUp(TestCase):
    def test_nowt_to_do(self) -> None:
        mailerd.clean_up()
        self.assertEqual(0, MailoutJob.objects.count())

    def test_clean_up_sending(self) -> None:
        job = MailoutJob.objects.create(
            subject="s",
            body_text="t",
            body_html="h",
            send_html=True,
            send_at=timezone.now() - timedelta(days=1),
            state=MailoutJob.SendState.SENDING,
        )
        mailerd.clean_up()
        job.refresh_from_db()
        self.assertEqual(MailoutJob.SendState.FAILED, job.state)

    def test_clean_up_cancelled(self) -> None:
        job = MailoutJob.objects.create(
            subject="s",
            body_text="t",
            body_html="h",
            send_html=True,
            send_at=timezone.now() - timedelta(days=1),
            state=MailoutJob.SendState.CANCELLING,
        )
        mailerd.clean_up()
        job.refresh_from_db()
        self.assertEqual(MailoutJob.SendState.CANCELLED, job.state)

    def test_clean_up_leaves_other_things_alone(self) -> None:
        states = [
            MailoutJob.SendState.PENDING,
            MailoutJob.SendState.SENT,
            MailoutJob.SendState.FAILED,
            MailoutJob.SendState.CANCELLED,
        ]
        for state in states:
            with self.subTest(state):
                job = MailoutJob.objects.create(
                    subject="s",
                    body_text="t",
                    body_html="h",
                    send_html=True,
                    send_at=timezone.now() - timedelta(days=1),
                    state=state,
                )
                mailerd.clean_up()
                job.refresh_from_db()
                self.assertEqual(state, job.state)


class TestRunJob(MembersTestsMixin, TestCase):

    @patch("toolkit.mailer.mailerd.send_mailout_to")
    def test_run_job(self, send_mock) -> None:
        job = MailoutJob.objects.create(
            subject="s",
            body_text="t",
            body_html="h",
            send_html=True,
            send_at=timezone.now(),
        )
        self.assertEqual(MailoutJob.SendState.PENDING, job.state)

        mailerd.run_job(job)
        send_mock.assert_called_once()
        self.assertEqual(job, send_mock.call_args[0][0])
        self.assertListEqual(
            list(Member.objects.mailout_recipients()),
            list(send_mock.call_args[0][1]),
        )
        self.assertEqual(
            settings.VENUE["mailout_delivery_report_to"],
            send_mock.call_args.kwargs["report_to"],
        )
        job.refresh_from_db()
        self.assertEqual(MailoutJob.SendState.SENDING, job.state)
        self.assertEqual(6, job.send_count)
        self.assertEqual(1, job.progress_pct)

    @patch("toolkit.mailer.mailerd.send_mailout_to")
    def test_run_job_no_recipients(self, send_mock) -> None:
        Member.objects.all().delete()
        self.assertEqual(0, Member.objects.count())

        job = MailoutJob.objects.create(
            subject="s",
            body_text="t",
            body_html="h",
            send_html=True,
            send_at=timezone.now(),
        )
        self.assertEqual(MailoutJob.SendState.PENDING, job.state)

        mailerd.run_job(job)
        send_mock.assert_not_called()

        job.refresh_from_db()
        self.assertEqual(MailoutJob.SendState.FAILED, job.state)
