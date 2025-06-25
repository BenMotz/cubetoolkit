from datetime import datetime, timezone, timedelta

from mock import patch

import fixtures
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings
from .common import ToolkitUsersFixture, FAKE_NOW
from ...mailer.models import MailoutJob


from .common import DiaryTestsMixin


class QueueMailoutTests(TestCase, fixtures.TestWithFixtures):
    def setUp(self):
        self.useFixture(ToolkitUsersFixture())
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")
        # Fake "now()" function to return a fixed time:
        self.time_patch = patch("django.utils.timezone.now")
        self.time_mock = self.time_patch.start()
        self.time_mock.return_value = FAKE_NOW

    def test_get_denied(self) -> None:
        url = reverse("queue-members-mailout")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_valid_delayed_send(self) -> None:
        url = reverse("queue-members-mailout")
        self.assertEqual(0, MailoutJob.objects.count())
        data = {
            "subject": "Yet another member's mailout",
            "body_text": "Let the bodies hit the floor\netc.",
            "body_html": "<h1>Should not be ignored</h1>",
            "send_at": "01/06/2025 22:11",
            "send_html": "on",
        }
        response = self.client.post(url, data=data)

        self.assertRedirects(response, reverse("mailer:jobs-list"))

        self.assertEqual(1, MailoutJob.objects.count())
        job = MailoutJob.objects.all()[0]
        self.assertEqual(data["subject"], job.subject)
        self.assertEqual(data["body_text"], job.body_text)
        self.assertEqual(data["body_html"], job.body_html)
        self.assertEqual(True, job.send_html)
        self.assertEqual(
            job.send_at,
            datetime(2025, 6, 1, 21, 11, tzinfo=timezone.utc),
        )

    def test_valid_send_now(self) -> None:
        url = reverse("queue-members-mailout", query={"send_at": "now"})
        self.assertEqual(0, MailoutJob.objects.count())
        data = {
            "subject": "Yet another member's mailout",
            "body_text": "Let the bodies hit the floor\netc.",
            "body_html": "<h1>Should not be ignored</h1>",
            "send_at": "01/06/1901 12:00",
            "send_html": "on",
        }
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse("mailer:jobs-list"))

        self.assertEqual(1, MailoutJob.objects.count())
        job = MailoutJob.objects.all()[0]
        self.assertEqual(data["subject"], job.subject)
        self.assertEqual(data["body_text"], job.body_text)
        self.assertEqual(data["body_html"], job.body_html)
        self.assertEqual(True, job.send_html)
        self.assertEqual(job.send_at, FAKE_NOW + timedelta(seconds=2))

    def test_invalid_date_in_past(self) -> None:
        url = reverse("queue-members-mailout")
        data = {
            "subject": "Yet another member's mailout",
            "body_text": "Let the bodies hit the floor\netc.",
            "body_html": "<h1>Should not be ignored</h1>",
            "send_at": (FAKE_NOW - timedelta(seconds=1)).strftime(
                "%d/%m/%Y %H:%M"
            ),
            "send_html": "on",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        self.assertFormError(
            response.context["form"], "send_at", "Must be in the future"
        )

        self.assertEqual(0, MailoutJob.objects.count())


class MailoutTests(DiaryTestsMixin, TestCase):
    def setUp(self):
        super().setUp()
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
            "\u010copy four summary\n"
        )
        # Urgh
        self.expected_mailout_event_html = """
            <textarea name="body_html" id="id_body_html" rows="10" cols="40">
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
            </td></tr></table><p>For complete listings
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
            <p>
            <em>
            \u010copy four summary
            </em>
            </p>
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
        self.assertContains(response, "Yet another member&#x27;s mailout")
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
                "send_html": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailout_send.html")
        # Text content:
        self.assertContains(response, "Yet another member&#x27;s mailout")
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
                "send_html": "on",
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
            response.context["form"], "subject", "This field is required."
        )
        self.assertFormError(
            response.context["form"], "body_text", "This field is required."
        )

    @override_settings(HTML_MAILOUT_ENABLED=True)
    def test_post_form_no_data_html_enabled(self):
        url = reverse("members-mailout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_mailout.html")

        self.assertFormError(
            response.context["form"], "subject", "This field is required."
        )
        self.assertFormError(
            response.context["form"], "body_text", "This field is required."
        )

    def test_invalid_method(self):
        url = reverse("members-mailout")
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)
