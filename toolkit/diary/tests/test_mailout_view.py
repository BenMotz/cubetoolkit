from __future__ import absolute_import

from mock import patch
import fixtures

from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings

import kombu.exceptions
import redis.exceptions

from toolkit.members.models import Member
from .common import DiaryTestsMixin, ToolkitUsersFixture


class MailoutTests(DiaryTestsMixin, TestCase):
    def setUp(self):
        super(MailoutTests, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

        # Fake "now()" function to return a fixed time:
        self.time_patch = patch("django.utils.timezone.now")
        self.time_mock = self.time_patch.start()
        self.time_mock.return_value = self._fake_now

        self.expected_mailout_subject_text = (
            '<input type="text" name="subject" value='
            '"Cube Microplex forthcoming events commencing Sunday 9 June"'
            ' required id="id_subject" maxlength="128" />'
        )

        self.expected_mailout_header_text = (
            "CUBE PROGRAMME OF EVENTS\n"
            "\n"
            "https://cubecinema.com/programme/\n"
            "\n"
        )

        self.expected_mailout_event_text = (
            "CUBE PROGRAMME OF EVENTS\n"
            "\n"
            "https://cubecinema.com/programme/\n"
            "\n"
            "2013\n"
            " JUNE\n"
            "  Sun 09 18:00 .... Event four titl\u0113\n"
            "\n"
            "* cheap night\n"
            "\n"
            "For complete listings including all future events, please visit:"
            "\n"
            "https://cubecinema.com/programme/\n"
            "\n"
            "----------------------------------------------------------------"
            "------------\n"
            "\n"
            "Pretitle four:\n"
            "EVENT FOUR TITL\u0112\n"
            " Posttitle four\n"
            "Film info for four\n"
            "\n"
            "Sun 9th / 6pm\n"
            "Tickets: \u00a3milliion per thing\n"
            "\n"
            "Event four C\u014dpy\n"
        )
        # Urgh
        self.expected_mailout_event_html = """
            <textarea name="body_html" id="id_body_html" rows="10" cols="40"
            required>
            <p><a href="https://www.cubecinema.com/programme/">
            Cube Cinema Programme</a></p><table><tr>
            <td colspan="3">
            2013
            </td></tr><tr><td colspan="3">
            JUNE
            </td></tr><tr><td>
            Sun 09&nbsp;
            </td><td>
            18:00 ....
            </td><td>
            Event four titl\u0113
            </td></tr></table><p>* cheap night</p><p>For complete listings
            including all future events, please visit:
            <a href="https://www.cubecinema.com/programme/">
            Cube Cinema Programme</a></p><hr><p>
            Pretitle four:<br><strong><a
            href="https://www.cubecinema.com/programme/event/,4/">EVENT
            FOUR TITL\u0112</a></strong><br>
            Posttitle four
            </p><p>
            Film info for four<br>
            Sun 9th / 6pm
            </p><p>
            Tickets: \u00a3milliion per thing<br></p>
            Event four C\u014dpy
            <hr><p>
            For complete and up to date listings, please visit:
            <a href="https://www.cubecinema.com/programme/">
            Cube Cinema Programme</a></p><p>Cube Microplex
            Cinema is located at:<br>
            Dove Street South<br>
            Bristol<br>
            BS2 8JD</p><p>
            Postal:<br>
            4 Princess Row<br>
            Bristol<br>
            BS2 8NQ
            </p><p><a href="https://www.cubecinema.com">
            www.cubecinema.com</a></p>
            <p>tel: 0117 907 4190</p>
            </textarea>"""

    def tearDown(self):
        self.time_patch.stop()

    # Tests of edit mailout / confirm mailout form ##########################

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_get_form_html_disabled(self):
        url = reverse("members-mailout")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")
        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(
            response, self.expected_mailout_subject_text, html=True
        )
        # Fairly general, to be insensitive to template/form changes:
        self.assertNotContains(response, "send_html")
        self.assertNotContains(response, "HTML email")

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_get_form_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")
        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(
            response, self.expected_mailout_event_html, html=True
        )
        self.assertContains(
            response, self.expected_mailout_subject_text, html=True
        )
        self.assertContains(
            response,
            '<input type="checkbox" name="send_html" '
            'checked id="id_send_html" />',
            html=True,
        )
        self.assertContains(
            response,
            '<h3><label for="id_body_html">Body of HTML email</label></h3>',
            html=True,
        )

    def test_get_form_custom_daysahead(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": 15})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(
            response, self.expected_mailout_subject_text, html=True
        )

    def test_get_form_invalid_daysahead(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": "monkey"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(
            response, self.expected_mailout_subject_text, html=True
        )

    def test_get_form_no_events(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": 1})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header_text)
        # NOT:
        self.assertNotContains(response, self.expected_mailout_event_text)

        # Expected subject - no "commencing" string:
        self.assertContains(
            response,
            self.expected_mailout_subject_text.replace(
                " commencing Sunday 9 June", ""
            ),
            html=True,
        )

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_html_disabled(self):
        url = reverse("members-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # Text content:
        self.assertContains(response, "Yet another member&#39;s mailout")
        self.assertContains(response, "Let the bodies hit the floor\netc.")
        # HTML content:
        self.assertNotContains(response, "HTML Body")

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_post_form_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "body_html": "<h1>Should not be ignored</h1>",
                "send_html": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # Text content:
        self.assertContains(response, "Yet another member&#39;s mailout")
        self.assertContains(response, "Let the bodies hit the floor\netc.")
        # HTML content:
        self.assertContains(
            response, '<p class="label">HTML Body:</p>', html=True
        )
        self.assertContains(
            response,
            '<p class="mail" id="body_html">'
            "&lt;h1&gt;Should not be ignored&lt;/h1&gt;</p>",
            html=True,
        )

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_html_enabled_do_not_send_html(self):
        url = reverse("members-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "body_html": "<h1>Should be ignored</h1>",
                "send_html": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # HTML content:
        self.assertNotContains(response, "HTML Body")
        self.assertNotContains(response, "Should be ignored")

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_html_disabled_html_body_ignored(self):
        url = reverse("members-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "body_html": "<h1>Should be ignored</h1>",
                "send_html": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # HTML content:
        self.assertNotContains(response, "HTML Body")
        self.assertNotContains(response, "Should be ignored")

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_no_data_html_disabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertFormError(
            response, "form", "subject", "This field is required."
        )
        self.assertFormError(
            response, "form", "body_text", "This field is required."
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_post_form_no_data_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertFormError(
            response, "form", "subject", "This field is required."
        )
        self.assertFormError(
            response, "form", "body_text", "This field is required."
        )

    def test_invalid_method(self):
        url = reverse("members-mailout")
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)

    # Tests of send mailout / Ajax form ######################################
    def test_exec_view_invalid_method(self):
        url = reverse("exec-mailout")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_exec_view_invalid_content_html_disabled(self):
        url = reverse("exec-mailout")
        # No data provided
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "status": "error",
                "errors": {
                    "body_text": ["This field is required."],
                    "subject": ["This field is required."],
                },
            },
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_exec_view_invalid_content_html_enabled(self):
        url = reverse("exec-mailout")
        # All data provided, except HTML content:
        response = self.client.post(
            url,
            data={
                "body_text": "Body text",
                "subject": "subject",
                # body_html is needed even if the option is false/missing;
                # u'send_html': u'true',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "status": "error",
                "errors": {
                    "body_html": ["This field is required."],
                },
            },
        )

    @patch("toolkit.members.tasks.send_mailout")
    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_exec_view_good_content_html_disabled(self, send_mailout_patch):
        send_mailout_patch.delay.return_value.task_id = "dummy-task-id"

        url = reverse("exec-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Mailout of the month",
                "body_text": "Blah\nBlah\nBlah",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "progress": 0, "task_id": "dummy-task-id"},
        )
        send_mailout_patch.delay.assert_called_once_with(
            "Mailout of the month",
            "Blah\nBlah\nBlah",
            # No HTML content:
            None,
        )

    @patch("toolkit.members.tasks.send_mailout")
    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_exec_view_good_content_html_enabled_send_html(
        self, send_mailout_patch
    ):
        send_mailout_patch.delay.return_value.task_id = "dummy-task-id"

        url = reverse("exec-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Mailout of the month",
                "body_text": "Blah\nBlah\nBlah",
                "body_html": "<p>Blah\nBlah\nBlah</p>",
                "send_html": "true",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "progress": 0, "task_id": "dummy-task-id"},
        )
        send_mailout_patch.delay.assert_called_once_with(
            "Mailout of the month",
            "Blah\nBlah\nBlah",
            # HTML content:
            "<p>Blah\nBlah\nBlah</p>",
        )

    @patch("toolkit.members.tasks.send_mailout")
    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_exec_view_good_content_html_enabled_do_not_send_html(
        self, send_mailout_patch
    ):
        send_mailout_patch.delay.return_value.task_id = "dummy-task-id"

        url = reverse("exec-mailout")
        response = self.client.post(
            url,
            data={
                "subject": "Mailout of the month",
                "body_text": "Blah\nBlah\nBlah",
                "body_html": "<p>Blah\nBlah\nBlah</p>",
                "send_html": "false",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "progress": 0, "task_id": "dummy-task-id"},
        )
        send_mailout_patch.delay.assert_called_once_with(
            "Mailout of the month",
            "Blah\nBlah\nBlah",
            # No HTML content:
            None,
        )

    def test_exec_view_get_progress_invalid_method(self):
        url = reverse("mailout-progress")
        response = self.client.post(url, data={"task_id": "dummy-task-id"})
        self.assertEqual(response.status_code, 405)

    @patch("toolkit.members.tasks.send_mailout.delay")
    def test_exec_view_task_start_failure(self, delay_patch):
        delay_patch.side_effect = kombu.exceptions.KombuError("No can do")

        url = reverse("exec-mailout")
        response = self.client.post(
            url, data={"subject": "S", "body_text": "B", "body_html": "B"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": True,
                "error_msg": "Failed starting task: No can do",
                "status": "error",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress(self, async_result_patch):
        async_result_patch.return_value.state = "PROGRESS10"
        async_result_patch.return_value.task_id = "dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": False,
                "error": None,
                "error_msg": None,
                "sent_count": None,
                "progress": 10,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_pending(self, async_result_patch):
        async_result_patch.return_value.state = "PENDING"
        async_result_patch.return_value.task_id = "dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": False,
                "error": None,
                "error_msg": None,
                "sent_count": None,
                "progress": 0,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure(self, async_result_patch):
        async_result_patch.return_value.state = "FAILURE"
        async_result_patch.return_value.task_id = "dummy-task-id"
        async_result_patch.return_value.result = IOError("This could happen")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": True,
                "error_msg": "This could happen",
                "sent_count": None,
                "progress": 0,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure_no_result(
        self, async_result_patch
    ):
        async_result_patch.return_value.state = "FAILURE"
        async_result_patch.return_value.task_id = "dummy-task-id"
        async_result_patch.return_value.result = None

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": True,
                "error_msg": "Failed: Unknown error",
                "sent_count": None,
                "progress": 0,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure_redis_error(
        self, async_result_patch
    ):
        async_result_patch.side_effect = redis.exceptions.ConnectionError(
            "nope"
        )

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": True,
                "error_msg": "Failed connecting to redis to retrieve job status: nope",
                "sent_count": 0,
                "progress": 0,
                "task_id": u"dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete(self, async_result_patch):
        async_result_patch.return_value.state = "SUCCESS"
        async_result_patch.return_value.task_id = "dummy-task-id"
        async_result_patch.return_value.result = (False, 321, "Ok")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": False,
                "error_msg": "Ok",
                "sent_count": 321,
                "progress": 100,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete_bad_result(
        self, async_result_patch
    ):
        async_result_patch.return_value.state = "SUCCESS"
        async_result_patch.return_value.task_id = "dummy-task-id"
        async_result_patch.return_value.result = "Nu?"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": True,
                "error_msg": "Couldn't retrieve status from completed job",
                "sent_count": 0,
                "progress": 100,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete_error(self, async_result_patch):
        async_result_patch.return_value.state = "SUCCESS"
        async_result_patch.return_value.task_id = "dummy-task-id"
        async_result_patch.return_value.result = (True, 322, "Error message")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": True,
                "error": True,
                "error_msg": "Error message",
                "sent_count": 322,
                "progress": 100,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_bad_celery_progress_data(self, async_result_patch):
        async_result_patch.return_value.state = "PROGRESS"
        async_result_patch.return_value.task_id = "dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": False,
                "error": None,
                "error_msg": None,
                "sent_count": None,
                "progress": 0,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_bad_celery_data(self, async_result_patch):
        async_result_patch.return_value.state = "garbage scow"
        async_result_patch.return_value.task_id = "dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={"task_id": "dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "complete": False,
                "error": None,
                "error_msg": None,
                "sent_count": None,
                "progress": 0,
                "task_id": "dummy-task-id",
            },
            response.json(),
        )


class MailoutTestSendViewTests(TestCase, fixtures.TestWithFixtures):
    def setUp(self):
        self.useFixture(ToolkitUsersFixture())

        self.url = reverse("mailout-test-send")

        self.member = Member(
            name="Member One",
            email="one@example.com",
            number="1",
            postcode="BS1 1AA",
        )
        self.member.save()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

        self.send_patch = patch("toolkit.members.tasks.send_mailout_to")
        self.send_mock = self.send_patch.start()

    def tearDown(self):
        self.send_patch.stop()

    def test_no_get(self):
        response = self.client.get(self.url)
        # 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    @override_settings(HTML_MAILOUT_ENABLED=False)
    @patch("toolkit.diary.mailout_views.Member")
    def test_success_html_disabled(self, member_mock):
        self.send_mock.return_value = (False, 1, None)
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "address": "one@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "ok",
                "errors": None,
            },
        )
        self.send_mock.assert_called_once_with(
            "Yet another member's mailout",
            "Let the bodies hit the floor\netc.",
            None,
            member_mock.objects.filter.return_value.__getitem__.return_value,
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    @patch("toolkit.diary.mailout_views.Member")
    def test_success_html_enabled(self, member_mock):
        self.send_mock.return_value = (False, 1, None)
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "body_html": "<h1>My HTML email</h1>",
                "send_html": "true",
                "address": "one@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "ok",
                "errors": None,
            },
        )
        self.send_mock.assert_called_once_with(
            "Yet another member's mailout",
            "Let the bodies hit the floor\netc.",
            "<h1>My HTML email</h1>",
            member_mock.objects.filter.return_value.__getitem__.return_value,
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    @patch("toolkit.diary.mailout_views.Member")
    def test_success_html_enabled_do_not_send_html(self, member_mock):
        self.send_mock.return_value = (False, 1, None)
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "body_html": "<h1>My HTML email</h1>",
                "send_html": "false",
                "address": "one@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "ok",
                "errors": None,
            },
        )
        self.send_mock.assert_called_once_with(
            "Yet another member's mailout",
            "Let the bodies hit the floor\netc.",
            None,
            member_mock.objects.filter.return_value.__getitem__.return_value,
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_missing_html(self):
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "address": "one@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "errors": "body_html: "
                '<ul class="errorlist"><li>This field is required.</li></ul>',
                "status": "error",
            },
        )
        self.send_mock.assert_not_called()

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_success_with_message(self):
        self.send_mock.return_value = (False, 1, "Message of success")
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "address": "one@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "ok",
                "errors": "Message of success",
            },
        )

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_failed_send(self):
        self.send_mock.return_value = (True, None, "Failed for some reason")
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "address": "one@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "error",
                "errors": "Failed for some reason",
            },
        )

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_no_member(self):
        self.send_mock.return_value = (False, None, None)
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "address": "two@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "error",
                "errors": "No member found with given email address",
            },
        )

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_bad_email(self):
        self.send_mock.return_value = (False, None, None)
        response = self.client.post(
            self.url,
            data={
                "subject": "Yet another member's mailout",
                "body_text": "Let the bodies hit the floor\netc.",
                "address": "dodgy",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            {
                "status": "error",
                "errors": 'address: <ul class="errorlist"><li>'
                "Enter a valid email address.</li></ul>",
            },
        )
