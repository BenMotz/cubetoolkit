import email.parser
import email.header
import smtplib
from datetime import timedelta
from mock import patch, Mock

from django.core import mail
from django.conf import settings
from django.test import TestCase
import django.utils.timezone

from ...members.tests.common import MembersTestsMixin
from ...members.models import Member
from ..mailerd import send_mailout_to
from ..models import MailoutJob


SUMMARY_RECIPIENT = "cubeadmin@example.com"


class TestSendMailoutTo(MembersTestsMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.assertTrue(
            self.client.login(username="admin", password="T3stPassword!")
        )

    def _assert_mail_as_expected(
        self,
        msgstr: str,
        is_utf8: bool,
        from_addr: str,
        dest_addr: str,
        body_contains: str,
        expected_subject: str,
    ) -> None:
        message = email.parser.Parser().parsestr(msgstr)

        self.assertEqual(message.get_content_type(), "text/plain")
        self.assertFalse(message.is_multipart())
        # It's always UTF-8, even if the content is ASCII:
        self.assertEqual(message.get_charsets(), ["utf-8"])
        if is_utf8:
            self.assertEqual(message["Content-Transfer-Encoding"], "8bit")
        else:
            self.assertEqual(message["Content-Transfer-Encoding"], "7bit")
        self.assertEqual(message["From"], from_addr)
        self.assertEqual(message["To"], dest_addr)

        body = message.get_payload()
        subject = email.header.decode_header(message["Subject"])

        self.assertIn(body_contains, body)
        subject = (
            subject[0][0].decode(subject[0][1])
            if subject[0][1]
            else subject[0][0]
        )
        self.assertEqual(subject, expected_subject)

    def _assert_mail_sent(
        self,
        subject: str,
        body_text: str,
        body_html: str | None,
        is_utf8: bool,
    ) -> None:
        # Sent 6 mails, plus one summary:
        self.assertEqual(len(mail.outbox), 7)

        for msg in mail.outbox[:-1]:  # the summary is never html
            if body_html:
                self.assertIsInstance(msg, mail.EmailMultiAlternatives)
            else:
                self.assertIsInstance(msg, mail.EmailMessage)

        # Validate summary:
        summary_mail = mail.outbox[6]
        self.assertIsInstance(summary_mail, mail.EmailMessage)
        self.assertEqual(
            summary_mail.from_email, settings.VENUE["mailout_from_address"]
        )
        self.assertEqual(summary_mail.to, [SUMMARY_RECIPIENT])
        # Check mail twice, to check for each bit of expected text in the body;
        # The mail count:
        self._assert_mail_as_expected(
            str(summary_mail.message()),
            is_utf8,
            settings.VENUE["mailout_from_address"],
            SUMMARY_RECIPIENT,
            "6 copies of the following were sent out on Cube members list",
            subject,
        )
        # And the actual body text:
        self._assert_mail_as_expected(
            str(summary_mail.message()),
            is_utf8,
            settings.VENUE["mailout_from_address"],
            SUMMARY_RECIPIENT,
            body_text,
            subject,
        )

    def _test_send(
        self,
        subject: str,
        body_text: str,
        body_html: str = "",
        send_html: bool = False,
    ) -> MailoutJob:
        job = MailoutJob(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            send_html=send_html,
            send_at=django.utils.timezone.now() + timedelta(days=1),
        )
        job.do_sending(sent=0, total=0)
        job.save()
        recipients = Member.objects.mailout_recipients()
        send_mailout_to(job, recipients, report_to=SUMMARY_RECIPIENT)
        return job

    def test_send_unicode(self) -> None:
        subject = "The Subject \u2603!"
        body = "The Body!\nThat will be \u20ac1, please\nTa \u2603!"
        job = self._test_send(subject, body)
        self._assert_mail_sent(subject, body, None, True)

        self.assertEqual(6, job.send_count)
        self.assertEqual(MailoutJob.SendState.SENT, job.state)
        self.assertEqual("Complete", job.status)

    def test_send_ascii(self) -> None:
        subject = "The Subject!"
        body = "The Body!\nThat will be $1, please\nTa!"
        self._test_send(subject, body)
        self._assert_mail_sent(subject, body, None, False)

    def test_send_iso88591_subj(self) -> None:
        subject = "The \xa31 Subject!"
        body = "The Body!\nThat will be $1, please\nTa!"
        self._test_send(subject, body)
        self._assert_mail_sent(subject, body, None, False)

    def test_send_html(self) -> None:
        subject = "The Subject \u2603!"
        body = "The Body!\nThat will be \u20ac1, please\nTa \u2603!"
        body_html = "<h1>Body<\\h1>\n<p>That will be \u20ac1, please\nTa</p>"
        self._test_send(subject, body, body_html, send_html=True)
        self._assert_mail_sent(subject, body, body_html, True)

    @patch("toolkit.mailer.mailerd.get_connection")
    def test_connect_fail(self, connection_mock: Mock) -> None:
        connection_mock.return_value.open.side_effect = (
            smtplib.SMTPConnectError(101, "Blah")
        )

        job = self._test_send(
            subject="The \xa31 Subject!",
            body_text="The Body!\nThat will be $1, please\nTa!",
        )

        self.assertEqual(MailoutJob.SendState.FAILED, job.state)
        self.assertEqual(
            "Failed to connect to SMTP server: (101, 'Blah')", job.status
        )
        self.assertEqual(0, job.send_count)

    @patch("django.core.mail.backends.base.BaseEmailBackend.close")
    def test_disconnect_fail(self, close_mock: Mock) -> None:
        subject = "The Subject \u2603!"
        body = "The Body!\nThat will be \u20ac1, please\nTa \u2603!"
        close_mock.side_effect = smtplib.SMTPServerDisconnected(
            "Already disconnected?"
        )

        job = self._test_send(subject, body)
        self._assert_mail_sent(subject, body, None, True)

        close_mock.assert_called_once()

        self.assertEqual(MailoutJob.SendState.SENT, job.state)
        self.assertEqual("Complete", job.status)

    @patch("toolkit.mailer.mailerd.get_connection")
    def test_send_fail(self, connection_mock: Mock) -> None:
        exception = smtplib.SMTPException("Something failed")
        connection_mock.return_value.send_messages.side_effect = exception

        job = self._test_send(
            "The \xa31 Subject!",
            "The Body!\nThat will be $1, please\nTa!",
        )

        # Overall, operation succeeded:
        self.assertEqual(MailoutJob.SendState.SENT, job.state)
        self.assertEqual("Complete", job.status)

        # Check errors are in the report message:
        report = connection_mock.return_value.send_messages.call_args[0][0][0]
        expected = "6 errors:\n" + "\n".join([str(exception)] * 6)
        self.assertIn(expected, report.body)

    @patch("toolkit.mailer.mailerd.get_connection")
    def test_send_fail_disconnected(self, connection_mock: Mock) -> None:
        connection_mock.return_value.send_messages.side_effect = (
            smtplib.SMTPServerDisconnected("Something failed")
        )

        job = self._test_send(
            "The \xa31 Subject!",
            "The Body!\nThat will be $1, please\nTa!",
        )

        self.assertEqual(MailoutJob.SendState.FAILED, job.state)
        self.assertEqual("Mailout job died: 'Something failed'", job.status)

    @patch("toolkit.mailer.mailerd.get_connection")
    def test_random_error(self, connection_mock: Mock) -> None:
        # Test a non SMTP error
        connection_mock.return_value.send_messages.side_effect = IOError(
            "something"
        )

        job = self._test_send(
            "The \xa31 Subject!",
            "The Body!\nThat will be $1, please\nTa!",
        )

        self.assertEqual(MailoutJob.SendState.FAILED, job.state)
        self.assertEqual("Mailout job died: 'something'", job.status)

    def test_no_recipients(self) -> None:
        Member.objects.all().delete()
        job = self._test_send(
            "The \xa31 Subject!",
            "The Body!\nThat will be $1, please\nTa!",
        )
        self.assertEqual(MailoutJob.SendState.SENT, job.state)
        self.assertEqual("Complete", job.status)
        self.assertEqual(0, job.send_count)

    def test_send_unicode_email_address(self) -> None:
        subject = "The Subject \u2603!"
        body = "The Body!\nThat will be \u20ac1, please\nTa \u2603!"

        member = Member.objects.get(id=1)
        member.email = "\u0205ne@\u0205xample.com"
        member.save()

        job = self._test_send(subject, body)

        self._assert_mail_sent(subject, body, None, True)
        self.assertEqual(mail.outbox[0].to, ["\u0205ne@\u0205xample.com"])

        self.assertEqual(MailoutJob.SendState.SENT, job.state)
        self.assertEqual("Complete", job.status)
        self.assertEqual(6, job.send_count)
