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

    def _job(self) -> MailoutJob:
        return MailoutJob(
            send_at=django.utils.timezone.now() + timedelta(days=1),
            send_html=True,
            subject="subject",
            body_text="Body",
            body_html="<p>Body</p>",
        )

    def _create_jobs(self, extra_pending=0) -> list[MailoutJob]:
        jobs = [self._job() for _ in range(6 + extra_pending)]
        # 0 - pending
        # 1 - sending
        jobs[1].do_sending(sent=0, total=100)
        # 2 - cancelling

        jobs[2].do_sending(sent=0, total=100)
        jobs[2].do_cancel()
        # 3 - sent
        jobs[3].do_sending(sent=0, total=100)
        jobs[3].do_complete(sent=0x100)

        # 4 - failed
        jobs[4].do_fail(status="borked")

        # 5 - cancelled
        jobs[5].do_cancel()

        for job in jobs:
            job.save()

        return jobs

    def test_all_jobs(self) -> None:
        self._create_jobs()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list.html")
        self.assertTemplateUsed(response, "jobs-list-table.html")

        for job in MailoutJob.objects.all():
            self.assertContains(response, f"<td>{job.pk}</td>", html=True)

        self.assertContains(response, f"<td>FAILED: borked</td>", html=True)

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

        for job in MailoutJob.objects.all():
            self.assertContains(response, f"<td>{job.pk}</td>", html=True)

        self.assertContains(response, f"<td>FAILED: borked</td>", html=True)
        self.assertNotContains(response, 'hx-trigger="every 1s"')

    def test_table_fragment_polling_enabled(self) -> None:
        self._create_jobs()

        url = reverse("mailer:jobs-table", query={"poll-for-updates": "on"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")

        self.assertContains(response, 'hx-trigger="every 1s"')

    def test_no_pagination_nav_single_page(self) -> None:
        self._create_jobs()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Six jobs fit on a single page: no pagination controls.
        self.assertNotContains(response, "Page 1 of")

    def test_pagination_first_page(self) -> None:
        jobs = self._create_jobs(extra_pending=9)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 1 of 2")
        # Newest 10 (highest pks) shown, oldest 5 not.
        for job in jobs[10:]:
            self.assertContains(response, f"<td>{job.pk}</td>", html=True)
        for job in jobs[:5]:
            self.assertNotContains(response, f"<td>{job.pk}</td>", html=True)
        self.assertContains(response, "?page=2")

    def test_pagination_second_page(self) -> None:
        jobs = self._create_jobs(extra_pending=9)

        url = reverse("mailer:jobs-list", query={"page": "2"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 2 of 2")
        # Oldest 5 (lowest pks) shown on the second page.
        for job in jobs[:5]:
            self.assertContains(response, f"<td>{job.pk}</td>", html=True)
        for job in jobs[10:]:
            self.assertNotContains(response, f"<td>{job.pk}</td>", html=True)

    def test_pagination_out_of_range_page(self) -> None:
        self._create_jobs(extra_pending=9)
        # An out-of-range page falls back to the last page, not a 404.
        url = reverse("mailer:jobs-list", query={"page": "999"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 2 of 2")

    def test_pagination_invalid_page(self) -> None:
        jobs = self._create_jobs(extra_pending=9)
        # A non-numeric page falls back to the first page, not a 404.
        url = reverse("mailer:jobs-list", query={"page": "not-a-number"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 1 of 2")

    def test_table_fragment_pagination(self) -> None:
        jobs = self._create_jobs(extra_pending=9)

        url = reverse("mailer:jobs-table", query={"page": "2"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs-list-table.html")
        self.assertContains(response, "Page 2 of 2")
        for job in jobs[:5]:
            self.assertContains(response, f"<td>{job.pk}</td>", html=True)
