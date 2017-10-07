from __future__ import absolute_import
import json

from mock import patch
import fixtures

from django.test import TestCase
from django.core.urlresolvers import reverse

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

        self.expected_mailout_subject = (
            'type="text" value="CUBE Microplex forthcoming events'
            ' commencing Sunday 9 June"'
        )

        self.expected_mailout_header = (
            u"CUBE PROGRAMME OF EVENTS\n"
            u"\n"
            u"http://www.cubecinema.com/programme/\n"
            u"\n"
        )

        self.expected_mailout_event = (
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

    def tearDown(self):
        self.time_patch.stop()

    # Tests of edit mailout / confirm mailout form ##########################

    def test_get_form(self):
        url = reverse("members-mailout")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")
        self.assertContains(response, self.expected_mailout_header)
        self.assertContains(response, self.expected_mailout_event)
        self.assertContains(response, self.expected_mailout_subject)

    def test_get_form_custom_daysahead(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": 15})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header)
        self.assertContains(response, self.expected_mailout_event)
        self.assertContains(response, self.expected_mailout_subject)

    def test_get_form_invalid_daysahead(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": "monkey"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header)
        self.assertContains(response, self.expected_mailout_event)
        self.assertContains(response, self.expected_mailout_subject)

    def test_get_form_no_events(self):
        url = reverse("members-mailout")
        response = self.client.get(url, data={"daysahead": 1})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertContains(response, self.expected_mailout_header)
        # NOT:
        self.assertNotContains(response, self.expected_mailout_event)

        # Expected subject - no "commencing" string:
        self.assertContains(response,
                            'type="text" '
                            'value="CUBE Microplex forthcoming events"')

    def test_post_form(self):
        url = reverse("members-mailout")
        response = self.client.post(url, data={
            'subject': "Yet another member's mailout",
            'body': u"Let the bodies hit the floor\netc."
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")

    def test_post_form_no_data(self):
        url = reverse("members-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertFormError(response, 'form', 'subject',
                             u'This field is required.')
        self.assertFormError(response, 'form', 'body',
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

    def test_exec_view_invalid_content(self):
        url = reverse("exec-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        response = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response, {
            u"status": u"error",
            u"errors": {
                u"body": [u"This field is required."],
                u"subject": [u"This field is required."]
            }
        })

    @patch("toolkit.members.tasks.send_mailout")
    def test_exec_view_good_content(self, send_mailout_patch):
        send_mailout_patch.delay.return_value.task_id = u'dummy-task-id'

        url = reverse("exec-mailout")
        response = self.client.post(url, data={
            u"subject": u"Mailout of the month",
            u"body": u"Blah\nBlah\nBlah",
        })

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))

        self.assertEqual(response_data, {
            u"status": u"ok",
            u"progress": 0,
            u"task_id": u"dummy-task-id"
        })

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
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 10,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_pending(self, async_result_patch):
        async_result_patch.return_value.state = u"PENDING"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure(self, async_result_patch):
        async_result_patch.return_value.state = u"FAILURE"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = IOError("This could happen")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': "This could happen",
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_failure_no_result(self,
                                                      async_result_patch):
        async_result_patch.return_value.state = u"FAILURE"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = None

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': "Failed: Unknown error",
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete(self, async_result_patch):
        async_result_patch.return_value.state = u"SUCCESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = (False, 321, "Ok")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': True,
            u'error': False,
            u'error_msg': u'Ok',
            u'sent_count': 321,
            u'progress': 100,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete_bad_result(self,
                                                        async_result_patch):
        async_result_patch.return_value.state = u"SUCCESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = "Nu?"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': u"Couldn't retrieve status from completed job",
            u'sent_count': 0,
            u'progress': 100,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_progress_complete_error(self, async_result_patch):
        async_result_patch.return_value.state = u"SUCCESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"
        async_result_patch.return_value.result = (True, 322, "Error message")

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': True,
            u'error': True,
            u'error_msg': u'Error message',
            u'sent_count': 322,
            u'progress': 100,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_bad_celery_progress_data(self, async_result_patch):
        async_result_patch.return_value.state = u"PROGRESS"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response_data)

    @patch("celery.result.AsyncResult")
    def test_exec_view_get_bad_celery_data(self, async_result_patch):
        async_result_patch.return_value.state = u"garbage scow"
        async_result_patch.return_value.task_id = u"dummy-task-id"

        url = reverse("mailout-progress")
        response = self.client.get(url, data={u"task_id": u"dummy-task-id"})

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual({
            u'complete': False,
            u'error': None,
            u'error_msg': None,
            u'sent_count': None,
            u'progress': 0,
            u'task_id': u'dummy-task-id'
        }, response_data)


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

    def test_success(self):
        self.send_mock.return_value = (False, 1, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 'ok',
            'errors': None,
        })

    def test_success_with_message(self):
        self.send_mock.return_value = (False, 1, "Message of success")
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 'ok',
            'errors': "Message of success",
        })

    def test_failed_send(self):
        self.send_mock.return_value = (True, None, u"Failed for some reason")
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body': u"Let the bodies hit the floor\netc.",
            'address': u"one@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 'error',
            'errors': 'Failed for some reason',
        })

    def test_no_member(self):
        self.send_mock.return_value = (False, None, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body': u"Let the bodies hit the floor\netc.",
            'address': u"two@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 'error',
            'errors': 'No member found with given email address',
        })

    def test_bad_email(self):
        self.send_mock.return_value = (False, None, None)
        response = self.client.post(self.url, data={
            'subject': u"Yet another member's mailout",
            'body': u"Let the bodies hit the floor\netc.",
            'address': u"dodgy",
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 'error',
            'errors':  u'address: <ul class="errorlist"><li>'
                       u'Enter a valid email address.</li></ul>'
        })
