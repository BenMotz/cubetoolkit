from __future__ import absolute_import

from mock import patch
import fixtures

from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings

from toolkit.members.models import Member
from .common import DiaryTestsMixin, ToolkitUsersFixture


class MailoutTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(MailoutTests, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

        # Fake "now()" function to return a fixed time:
        self.time_patch = patch('django.utils.timezone.now')
        self.time_mock = self.time_patch.start()
        self.time_mock.return_value = self._fake_now

        self.expected_mailout_subject_text = (
            '<input type="text" name="subject" value='
            '"Cube Microplex forthcoming events commencing Sunday 9 June"'
            ' required id="id_subject" maxlength="128" />'
        )

        self.expected_mailout_header_text = (
            u"CUBE PROGRAMME OF EVENTS\n"
            u"\n"
            u"http://www.cubecinema.com/programme/\n"
            u"\n"
        )

        self.expected_mailout_event_text = (
            u"CUBE PROGRAMME OF EVENTS\n"
            u"\n"
            u"http://www.cubecinema.com/programme/\n"
            u"\n"
            u"2013\n"
            u" JUNE\n"
            u"  Sun 09 18:00 .... Event four titl\u0113\n"
            u"\n"
            u"* cheap night\n"
            u"\n"
            u"For complete listings including all future events, please visit:"
            u"\n"
            u"http://www.cubecinema.com/programme/\n"
            u"\n"
            u"----------------------------------------------------------------"
            u"------------\n"
            u"\n"
            u"Pretitle four:\n"
            u"EVENT FOUR TITL\u0112\n"
            u" Posttitle four\n"
            u"Film info for four\n"
            u"\n"
            u"Sun 9th / 6pm\n"
            u"Tickets: \u00a3milliion per thing\n"
            u"\n"
            u"Event four C\u014dpy\n"
        )
        # Urgh
        self.expected_mailout_event_html = (u"""
            <textarea name="body_html" id="id_body_html" rows="10" cols="40"
            required>
            <p><a href="http://www.cubecinema.com/programme/">
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
            <a href="http://www.cubecinema.com/programme/">
            Cube Cinema Programme</a></p><hr><p>
            Pretitle four:<br><strong><a
            href="http://www.cubecinema.com/programme/event/,4/">EVENT
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
            <a href="http://www.cubecinema.com/programme/">
            Cube Cinema Programme</a></p><p>Cube Microplex
            Cinema is located at:<br>
            Dove Street South<br>
            Bristol<br>
            BS2 8JD</p><p>
            Postal:<br>
            4 Princess Row<br>
            Bristol<br>
            BS2 8NQ
            </p><p><a href="http://www.cubecinema.com">
            www.cubecinema.com</a></p>
            <p>tel: 0117 907 4190</p>
            </textarea>""")

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
        self.assertContains(response, self.expected_mailout_subject_text,
                            html=True)
        # Fairly general, to be insensitive to template/form changes:
        self.assertNotContains(response, 'send_html')
        self.assertNotContains(response, 'HTML email')

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_get_form_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")
        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(response, self.expected_mailout_event_html,
                            html=True)
        self.assertContains(response, self.expected_mailout_subject_text,
                            html=True)
        self.assertContains(response,
                            '<input type="checkbox" name="send_html" '
                            'checked id="id_send_html" />',
                            html=True)
        self.assertContains(
            response,
            '<h3><label for="id_body_html">Body of HTML email</label></h3>',
            html=True)

    def test_get_form_custom_daysahead(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": 15})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(response, self.expected_mailout_subject_text,
                            html=True)

    def test_get_form_invalid_daysahead(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": "monkey"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header_text)
        self.assertContains(response, self.expected_mailout_event_text)
        self.assertContains(response, self.expected_mailout_subject_text,
                            html=True)

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
                " commencing Sunday 9 June", ""), html=True)

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_html_disabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url, data={
            'subject': "Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc."
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # Text content:
        self.assertContains(response, u"Yet another member&#39;s mailout")
        self.assertContains(response, u"Let the bodies hit the floor\netc.")
        # HTML content:
        self.assertNotContains(response, u'HTML Body')

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_post_form_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url, data={
            'subject': "Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'body_html': u"<h1>Should not be ignored</h1>",
            'send_html': True
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # Text content:
        self.assertContains(response, u"Yet another member&#39;s mailout")
        self.assertContains(response, u'Let the bodies hit the floor\netc.')
        # HTML content:
        self.assertContains(response,
                            u'<p class="label">HTML Body:</p>',
                            html=True)
        self.assertContains(response,
                            u'<p class="mail" id="body_html">'
                            u'&lt;h1&gt;Should not be ignored&lt;/h1&gt;</p>',
                            html=True)

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_html_enabled_do_not_send_html(self):
        url = reverse("members-mailout")
        response = self.client.post(url, data={
            'subject': "Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'body_html': u"<h1>Should be ignored</h1>",
            'send_html': False
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # HTML content:
        self.assertNotContains(response, u'HTML Body')
        self.assertNotContains(response, u'Should be ignored')

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_html_disabled_html_body_ignored(self):
        url = reverse("members-mailout")
        response = self.client.post(url, data={
            'subject': "Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'body_html': u"<h1>Should be ignored</h1>",
            'send_html': True
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # HTML content:
        self.assertNotContains(response, u'HTML Body')
        self.assertNotContains(response, u'Should be ignored')

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_post_form_no_data_html_disabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertFormError(response, 'form', 'subject',
                             u'This field is required.')
        self.assertFormError(response, 'form', 'body_text',
                             u'This field is required.')

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_post_form_no_data_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertFormError(response, 'form', 'subject',
                             u'This field is required.')
        self.assertFormError(response, 'form', 'body_text',
                             u'This field is required.')

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

        self.assertEqual(response.json(), {
            u"status": u"error",
            u"errors": {
                u"body_text": [u"This field is required."],
                u"subject": [u"This field is required."]
            }
        })

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_exec_view_invalid_content_html_enabled(self):
        url = reverse("exec-mailout")
        # All data provided, except HTML content:
        response = self.client.post(url, data={
            u'body_text': u'Body text',
            u'subject': u'subject',
            # body_html is needed even if the option is false/missing;
            # u'send_html': u'true',
        })

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json(), {
            u"status": u"error",
            u"errors": {
                u"body_html": [u"This field is required."],
            }
        })

    @patch("toolkit.members.tasks.send_mailout")
    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_exec_view_good_content_html_disabled(self, send_mailout_patch):
        send_mailout_patch.delay.return_value.task_id = u'dummy-task-id'

        url = reverse("exec-mailout")
        response = self.client.post(url, data={
            u"subject": u"Mailout of the month",
            u"body_text": u"Blah\nBlah\nBlah",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            u"status": u"ok",
            u"progress": 0,
            u"task_id": u"dummy-task-id"
        })
        send_mailout_patch.delay.assert_called_once_with(
            u"Mailout of the month",
            u"Blah\nBlah\nBlah",
            # No HTML content:
            None)

    @patch("toolkit.members.tasks.send_mailout")
    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_exec_view_good_content_html_enabled_send_html(
            self, send_mailout_patch):
        send_mailout_patch.delay.return_value.task_id = u'dummy-task-id'

        url = reverse("exec-mailout")
        response = self.client.post(url, data={
            u"subject": u"Mailout of the month",
            u"body_text": u"Blah\nBlah\nBlah",
            u"body_html": u"<p>Blah\nBlah\nBlah</p>",
            u"send_html": u"true",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            u"status": u"ok",
            u"progress": 0,
            u"task_id": u"dummy-task-id"
        })
        send_mailout_patch.delay.assert_called_once_with(
            u"Mailout of the month",
            u"Blah\nBlah\nBlah",
            # HTML content:
            u"<p>Blah\nBlah\nBlah</p>")

    @patch("toolkit.members.tasks.send_mailout")
    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_exec_view_good_content_html_enabled_do_not_send_html(
            self, send_mailout_patch):
        send_mailout_patch.delay.return_value.task_id = u'dummy-task-id'

        url = reverse("exec-mailout")
        response = self.client.post(url, data={
            u"subject": u"Mailout of the month",
            u"body_text": u"Blah\nBlah\nBlah",
            u"body_html": u"<p>Blah\nBlah\nBlah</p>",
            u"send_html": u"false",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            u"status": u"ok",
            u"progress": 0,
            u"task_id": u"dummy-task-id"
        })
        send_mailout_patch.delay.assert_called_once_with(
            u"Mailout of the month",
            u"Blah\nBlah\nBlah",
            # No HTML content:
            None)

    def test_exec_view_get_progress_invalid_method(self):
        url = reverse("mailout-progress")
        response = self.client.post(url, data={u"task_id": u"dummy-task-id"})
        self.assertEqual(response.status_code, 405)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress(self, async_result_patch):
        async_result_patch.return_value.state = u"PROGRESS10"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 10,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_pending(self, async_result_patch):
        async_result_patch.return_value.state = u"PENDING"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure(self, async_result_patch):
        async_result_patch.return_value.state = u"FAILURE"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = IOError("This could happen")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': "This could happen",
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure_no_result(self,
                                                      async_result_patch):
        async_result_patch.return_value.state = u"FAILURE"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = None

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': "Failed: Unknown error",
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete(self, async_result_patch):
        async_result_patch.return_value.state = u"SUCCESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = (False, 321, "Ok")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': True,
            u'error': False,
            u'error_msg': u'Ok',
            u'sent_count': 321,
            u'progress': 100,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete_bad_result(self,
                                                        async_result_patch):
        async_result_patch.return_value.state = u"SUCCESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = "Nu?"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': u"Couldn't retrieve status from completed job",
            u'sent_count': 0,
            u'progress': 100,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete_error(self, async_result_patch):
        async_result_patch.return_value.state = u"SUCCESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = (True, 322, "Error message")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': u'Error message',
            u'sent_count': 322,
            u'progress': 100,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_bad_celery_progress_data(self, async_result_patch):
        async_result_patch.return_value.state = u"PROGRESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response.json())

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_bad_celery_data(self, async_result_patch):
        async_result_patch.return_value.state = u"garbage scow"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response.json())


class MailoutTestSendViewTests(TestCase, fixtures.TestWithFixtures):
    def setUp(self):
        self.useFixture(ToolkitUsersFixture())

        self.url = reverse("mailout-test-send")

        self.member = Member(name="Member One", email="one@example.com",
                             number="1", postcode="BS1 1AA")
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
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'ok',
            'errors': None,
        })
        self.send_mock.assert_called_once_with(
            u"Yet another member's mailout",
            u"Let the bodies hit the floor\netc.",
            None,
            member_mock.objects.filter.return_value.__getitem__.return_value
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    @patch("toolkit.diary.mailout_views.Member")
    def test_success_html_enabled(self, member_mock):
        self.send_mock.return_value = (False, 1, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'body_html': u"<h1>My HTML email</h1>",
            'send_html': u"true",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'ok',
            'errors': None,
        })
        self.send_mock.assert_called_once_with(
            u"Yet another member's mailout",
            u"Let the bodies hit the floor\netc.",
            u"<h1>My HTML email</h1>",
            member_mock.objects.filter.return_value.__getitem__.return_value
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    @patch("toolkit.diary.mailout_views.Member")
    def test_success_html_enabled_do_not_send_html(self, member_mock):
        self.send_mock.return_value = (False, 1, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'body_html': u"<h1>My HTML email</h1>",
            'send_html': u"false",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'ok',
            'errors': None,
        })
        self.send_mock.assert_called_once_with(
            u"Yet another member's mailout",
            u"Let the bodies hit the floor\netc.",
            None,
            member_mock.objects.filter.return_value.__getitem__.return_value
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_missing_html(self):
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            u'errors':
                u'body_html: '
                u'<ul class="errorlist"><li>This field is required.</li></ul>',
            u'status': u'error'
        })
        self.send_mock.assert_not_called()

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_success_with_message(self):
        self.send_mock.return_value = (False, 1, "Message of success")
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'ok',
            'errors': "Message of success",
        })

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_failed_send(self):
        self.send_mock.return_value = (True, None, u"Failed for some reason")
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'error',
            'errors': 'Failed for some reason',
        })

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_no_member(self):
        self.send_mock.return_value = (False, None, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'address': u"two@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'error',
            'errors': 'No member found with given email address',
        })

    @override_settings(HTML_MAILOUT_ENABLED=False)
    def test_bad_email(self):
        self.send_mock.return_value = (False, None, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body_text': u"Let the bodies hit the floor\netc.",
            'address': u"dodgy",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode("utf-8"), {
            'status': 'error',
            'errors':  u'address: <ul class="errorlist"><li>'
                       u'Enter a valid email address.</li></ul>'
        })
