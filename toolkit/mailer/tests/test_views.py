from datetime import timedelta
import fixtures
from django.test import TestCase
from django.urls import reverse
import django.utils.timezone

from toolkit.mailer.models import MailoutJob

from ...diary.tests.common import ToolkitUsersFixture


class TestPermissions(TestCase, fixtures.TestWithFixtures):
    def setUp(self) -> None:
        self.useFixture(ToolkitUsersFixture())

    def _assert_need_login(self, views_to_test):
        for view_name, kwargs in views_to_test.items():
            url = reverse(view_name, kwargs=kwargs)
            expected_redirect = reverse("login", query={"next": url})
            # Test GET:
            with self.subTest(f"GET {view_name} {url}"):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertRedirects(response, expected_redirect)
            # Test POST:
            with self.subTest(f"POST {view_name} {url}"):
                response = self.client.post(url)
                self.assertEqual(response.status_code, 302)
                self.assertRedirects(response, expected_redirect)

    def test_need_login(self):
        views = {
            "mailer:job-delete": {"job_id": 1},
            "mailer:jobs-list": {},
            "mailer:jobs-table": {},
        }
        self._assert_need_login(views)

    def test_need_write(self):
        self.client.login(username="read_only", password="T3stPassword!1")
        views = {
            "mailer:job-delete": {"job_id": 1},
        }
        self._assert_need_login(views)


class TestCancelJobView(TestCase, fixtures.TestWithFixtures):
    def setUp(self) -> None:
        self.useFixture(ToolkitUsersFixture())
        self.client.login(username="admin", password="T3stPassword!")

    def test_cancel(self) -> None:
        job = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        job.save()
        self.assertEqual(MailoutJob.objects.count(), 1)
        self.assertEqual(job.state, MailoutJob.SendState.PENDING)

        url = reverse("mailer:job-delete", kwargs={"job_id": job.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("mailer:jobs-list"))

        job.refresh_from_db()
        self.assertEqual(job.state, MailoutJob.SendState.CANCELLED)

    def test_cancel_non_existent(self) -> None:
        url = reverse("mailer:job-delete", kwargs={"job_id": 100})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_not_permitted(self) -> None:
        url = reverse("mailer:job-delete", kwargs={"job_id": 100})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)


class TestListJobView(TestCase, fixtures.TestWithFixtures):
    def setUp(self) -> None:
        self.useFixture(ToolkitUsersFixture())
        self.client.login(username="admin", password="T3stPassword!")
        self.url = reverse("mailer:jobs-list")

    def test_no_jobs(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list.html")
        self.assertTemplateUsed(response, "jobs-list-table.html")

    def _create_jobs(self) -> None:
        self.pending = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        self.pending.save()
        self.sending = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        self.sending.do_sending(sent=0, total=100)
        self.sending.save()
        self.cancelling = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        self.cancelling.do_sending(sent=0, total=100)
        self.cancelling.do_cancel()
        self.cancelling.save()
        self.sent = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        self.sent.do_sending(sent=0, total=100)
        self.sent.do_complete(sent=0x100)
        self.sent.save()
        self.failed = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        self.failed.do_fail(status="borked")
        self.failed.save()
        self.cancelled = MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )
        self.cancelled.do_cancel()
        self.cancelled.save()

    def test_all_jobs(self) -> None:
        self._create_jobs()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list.html")
        self.assertTemplateUsed(response, "jobs-list-table.html")

        expected = [
            self.pending.pk,
            self.sending.pk,
            self.cancelling.pk,
            self.failed.pk,
        ]
        unexpected = [
            self.cancelled.pk,
            self.sent.pk,
        ]
        for job_pk in expected:
            self.assertContains(response, f"<td>{job_pk}</td>", html=True)
        for job_pk in unexpected:
            self.assertNotContains(response, f"<td>{job_pk}</td>", html=True)

        self.assertContains(
            response, f"<td>FAILED<br>{self.failed.status}</td>", html=True
        )

    def test_table_fragment_no_jobs(self) -> None:
        url = reverse("mailer:jobs-table")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")

    def test_table_fragment_all_jobs(self) -> None:
        self._create_jobs()

        url = reverse("mailer:jobs-table")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")
        expected = [
            self.pending.pk,
            self.sending.pk,
            self.cancelling.pk,
        ]
        unexpected = [
            self.cancelled.pk,
            self.failed.pk,
            self.sent.pk,
        ]
        for job_pk in expected:
            self.assertContains(response, f"<td>{job_pk}</td>", html=True)
        for job_pk in unexpected:
            self.assertNotContains(response, f"<td>{job_pk}</td>", html=True)

        self.assertNotContains(response, 'hx-trigger="every 1s"')

    def test_table_fragment_show_completed(self) -> None:
        self._create_jobs()

        url = reverse("mailer:jobs-table", query={"show-completed": "on"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")

        for job in MailoutJob.objects.all():
            self.assertContains(response, f"<td>{job.pk}</td>")

        self.assertContains(
            response, f"<td>FAILED<br>{self.failed.status}</td>", html=True
        )

    def test_table_fragment_show_failed(self) -> None:
        self._create_jobs()

        url = reverse("mailer:jobs-table", query={"show-failed": "on"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")

        expected = [
            self.pending.pk,
            self.sending.pk,
            self.cancelling.pk,
            self.failed.pk,
        ]
        unexpected = [
            self.cancelled.pk,
            self.sent.pk,
        ]
        for job_pk in expected:
            self.assertContains(response, f"<td>{job_pk}</td>", html=True)
        for job_pk in unexpected:
            self.assertNotContains(response, f"<td>{job_pk}</td>", html=True)

        self.assertContains(
            response, f"<td>FAILED<br>{self.failed.status}</td>", html=True
        )

    def test_table_fragment_polling_enabled(self) -> None:
        self._create_jobs()

        url = reverse("mailer:jobs-table", query={"poll-for-updates": "on"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")

        self.assertContains(response, 'hx-trigger="every 1s"')
