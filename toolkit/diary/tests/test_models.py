from __future__ import absolute_import

import pytz
from datetime import datetime

from django.test import TestCase

from toolkit.diary.models import Showing

from .common import DiaryTestsMixin


class ShowingModelCustomQueryset(DiaryTestsMixin, TestCase):

    def test_manager_public(self):
        records = list(Showing.objects.public())
        # From the fixtures, there are 4 showings that are confirmed and not
        # private / hidden
        self.assertEqual(len(records), 4)
        for showing in records:
            self.assertTrue(showing.confirmed)
            self.assertFalse(showing.hide_in_programme)
            self.assertFalse(showing.event.private)

    def test_queryset_public(self):
        # Difference here is that we get a queryset, then use the public()
        # method on that (rather than using the public() method directly on
        # the manager)
        records = list(Showing.objects.all().public())
        # From the fixtures, there are 4 showings that are confirmed and not
        # private / hidden
        self.assertEqual(len(records), 4)
        for showing in records:
            self.assertTrue(showing.confirmed)
            self.assertFalse(showing.hide_in_programme)
            self.assertFalse(showing.event.private)

    def test_manager_not_cancelled(self):
        records = list(Showing.objects.not_cancelled())
        # From the fixtures, there are 7 showings that aren't cancelled
        self.assertEqual(len(records), 8)
        for showing in records:
            self.assertFalse(showing.cancelled)

    def test_manager_confirmed(self):
        records = list(Showing.objects.confirmed())
        # From the fixtures, there are 7 showings that are confirmed:
        self.assertEqual(len(records), 8)
        for showing in records:
            self.assertTrue(showing.confirmed)

    def test_manager_date_range(self):
        start = pytz.utc.localize(datetime(2013, 4, 2, 12, 0))
        end = pytz.utc.localize(datetime(2013, 4, 4, 12, 0))
        records = list(Showing.objects.start_in_range(start, end))
        # Expect 2 showings in this date range:
        self.assertEqual(len(records), 2)
        for showing in records:
            self.assertTrue(showing.start < end)
            self.assertTrue(showing.start > start)

    def test_queryset_chaining(self):
        start = pytz.utc.localize(datetime(2000, 4, 2, 12, 0))
        end = pytz.utc.localize(datetime(2013, 9, 1, 12, 0))
        records = list(Showing.objects.all()
                                      .public()
                                      .not_cancelled()
                                      .start_in_range(start, end)
                                      .confirmed())
        self.assertEqual(len(records), 3)
        for showing in records:
            self.assertTrue(showing.confirmed)
            self.assertFalse(showing.hide_in_programme)
            self.assertFalse(showing.event.private)
            self.assertFalse(showing.cancelled)
            self.assertTrue(showing.start < end)
            self.assertTrue(showing.start > start)
            self.assertTrue(showing.confirmed)
