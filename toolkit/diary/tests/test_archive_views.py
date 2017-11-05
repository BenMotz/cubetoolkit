from __future__ import absolute_import

from mock import patch

from django.test import TestCase
from django.urls import reverse

from .common import DiaryTestsMixin


class ArchiveViews(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(ArchiveViews, self).setUp()

        self.time_patch = patch('django.utils.timezone.now')
        time_mock = self.time_patch.start()
        time_mock.return_value = self._fake_now

    def tearDown(self):
        self.time_patch.stop()

    def test_view_index(self):
        url = reverse("archive-view-index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "showing_archive.html")

    def test_view_year(self):
        url = reverse("archive-view-year", kwargs={"year": "2013"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "showing_archive_year.html")

    def test_view_month(self):
        url = reverse("archive-view-month",
                      kwargs={"year": "2013", "month": "4"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "showing_archive_month.html")

    def test_view_search(self):
        url = reverse("archive-search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "showing_archive_search.html")

    def test_view_search_post_not_allowed(self):
        url = reverse("archive-search")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)

    def test_run_search_no_content(self):
        url = reverse("archive-search")
        response = self.client.get(url, data={"search_term": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "showing_archive_search.html")
        self.assertContains(response, "0 Results")

    def test_run_search(self):
        url = reverse("archive-search")
        response = self.client.get(url, data={"search_term": "event"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "showing_archive_search.html")
        self.assertContains(response, "4 Results")
