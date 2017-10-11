import smtplib
import email.parser
import email.header

from mock import patch, call

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

import toolkit.members.tasks
from toolkit.members.models import Member
from .common import MembersTestsMixin

class TestMemberMailoutTask(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestMemberMailoutTask, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def _assert_mail_as_expected(self, msgstr, is_utf8, from_addr, dest_addr,
                                 body_contains, expected_subject):
        message = email.parser.Parser().parsestr(msgstr)

        self.assertEqual(message.get_content_type(), 'text/plain')
        self.assertFalse(message.is_multipart())
        if is_utf8:
            self.assertEqual(message.get_charsets(), ["utf-8"])
            self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
        else:
            self.assertEqual(message.get_charsets(), ["us-ascii"])
            self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['From'], from_addr)
        self.assertEqual(message['To'], dest_addr)

        body = message.get_payload().decode("utf-8")
        subject = email.header.decode_header(message['Subject'])

        self.assertIn(body_contains, body)
        subject = subject[0][0].decode(subject[0][1]) if subject[
            0][1] else subject[0][0]
        self.assertEqual(subject, expected_subject)

    def _assert_mail_sent(self, result, current_task_mock, smtplib_mock,
                          subject, body, is_utf8):
        current_task_mock.update_state.assert_has_calls([
            call(state='PROGRESS017', meta={'total': 6, 'sent': 1}),
            call(state='PROGRESS034', meta={'total': 6, 'sent': 2}),
            call(state='PROGRESS051', meta={'total': 6, 'sent': 3}),
            call(state='PROGRESS067', meta={'total': 6, 'sent': 4}),
            call(state='PROGRESS084', meta={'total': 6, 'sent': 5}),
            # 101% complete! (ahem)
            call(state='PROGRESS101', meta={'total': 6, 'sent': 6})
        ])

        # Expect to have connected:
        smtplib_mock.assert_called_once_with('smtp.test', 8281)

        # Sent 6 mails, plus one summary:
        conn = smtplib_mock.return_value
        self.assertEqual(conn.sendmail.call_count, 7)

        # Validate summary:
        summary_mail_call = conn.sendmail.call_args_list[6]
        self.assertEqual(summary_mail_call[0][
                         0], settings.MAILOUT_FROM_ADDRESS)
        self.assertEqual(summary_mail_call[0][1], [
                         settings.MAILOUT_DELIVERY_REPORT_TO])
        # Check mail twice, to check for each bit of expected text in the body;
        # The mail count:
        self._assert_mail_as_expected(
            summary_mail_call[0][2],
            is_utf8,
            settings.MAILOUT_FROM_ADDRESS,
            settings.MAILOUT_DELIVERY_REPORT_TO,
            u"6 copies of the following were sent out on cube members list",
            subject
        )
        # And the actual body text:
        self._assert_mail_as_expected(
            summary_mail_call[0][2],
            is_utf8,
            settings.MAILOUT_FROM_ADDRESS,
            settings.MAILOUT_DELIVERY_REPORT_TO,
            body,
            subject
        )

        # Reported success:
        # False => no error, 6 == sent count:
        self.assertEqual(result, (False, 6, 'Ok'))

        # Disconnect:
        conn.quit.assert_called_once_with()

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_unicode(self, current_task_mock, smtplib_mock):
        subject = u"The Subject \u2603!"
        body = u"The Body!\nThat will be \u20ac1, please\nTa \u2603!"
        result = toolkit.members.tasks.send_mailout(subject, body)
        self._assert_mail_sent(result, current_task_mock,
                               smtplib_mock, subject, body, True)

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_ascii(self, current_task_mock, smtplib_mock):
        subject = u"The Subject!"
        body = u"The Body!\nThat will be $1, please\nTa!"
        result = toolkit.members.tasks.send_mailout(subject, body)
        self._assert_mail_sent(result, current_task_mock,
                               smtplib_mock, subject, body, False)

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_iso88591_subj(self, current_task_mock, smtplib_mock):
        subject = u"The \xa31 Subject!"
        body = u"The Body!\nThat will be $1, please\nTa!"
        result = toolkit.members.tasks.send_mailout(subject, body)
        self._assert_mail_sent(result, current_task_mock,
                               smtplib_mock, subject, body, False)

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_connect_fail(self, current_task_mock, smtplib_mock):
        smtplib_mock.side_effect = smtplib.SMTPConnectError("Blah", 101)

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        self.assertEqual(
            result,
            (True, 0, "Failed to connect to SMTP server: ('Blah', 101)"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_fail(self, current_task_mock, smtplib_mock):
        smtplib_mock.return_value.sendmail.side_effect = smtplib.SMTPException(
            "Something failed", 101)

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        # Overall, operation succeeded:
        self.assertEqual(result, (False, 6, "Ok"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_fail_disconnected(self, current_task_mock, smtplib_mock):
        smtplib_mock.return_value.sendmail.side_effect = \
                smtplib.SMTPServerDisconnected("Something failed", 101)

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        self.assertEqual(
            result, (True, 0, "Mailout job died: ('Something failed', 101)"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_random_error(self, current_task_mock, smtplib_mock):
        # Test a non SMTP error
        smtplib_mock.return_value.sendmail.side_effect = IOError("something")

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        # Overall, operation succeeded:
        self.assertEqual(result, (True, 0, "Mailout job died: something"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_no_recipients(self, current_task_mock, smtplib_mock):
        Member.objects.all().delete()
        # Test a non SMTP error
        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        self.assertEqual(result, (True, 0, "No recipients found"))
