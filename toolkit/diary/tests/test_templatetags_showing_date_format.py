from __future__ import absolute_import

from datetime import datetime

import zoneinfo
from mock import Mock
from django.test import TestCase

from toolkit.diary.templatetags.showing_date_format import format_showing_dates


class TestShowingDateFormatFilter(TestCase):
    def setUp(self):
        self.tz = zoneinfo.ZoneInfo("Europe/London")

    def _run_filter_on_dates(self, date_list):
        mock_showings = [Mock(start=d) for d in date_list]
        return format_showing_dates(mock_showings)

    def _test_equiv(self, date_tuple_list, expected):
        date_list = [datetime(*t, tzinfo=self.tz) for t in date_tuple_list]
        self.assertEqual(expected, self._run_filter_on_dates(date_list))

    def test_no_showings(self):
        self._test_equiv([], "")

    def test_one_showing_on_the_hour(self):
        self._test_equiv([(2012, 1, 1, 10, 00)], "Sun 1st / 10am")

    def test_one_showing_off_the_hour(self):
        self._test_equiv([(2013, 2, 2, 20, 30)], "Sat 2nd / 8:30pm")

    def test_two_showings_seq(self):
        self._test_equiv(
            [
                (2013, 2, 2, 20, 00),
                (2013, 2, 3, 20, 00),
            ],
            "Sat 2nd, Sun 3rd / 8pm",
        )

    def test_two_showings_non_seq(self):
        self._test_equiv(
            [
                (2013, 2, 2, 20, 00),
                (2013, 2, 4, 20, 00),
            ],
            "Sat 2nd, Mon 4th / 8pm",
        )

    def test_two_showings_diff_time(self):
        self._test_equiv(
            [
                (2013, 2, 2, 20, 00),
                (2013, 2, 3, 20, 30),
            ],
            "Sat 2nd / 8pm, Sun 3rd / 8:30pm",
        )

    def test_three_showings_seq(self):
        self._test_equiv(
            [
                (2015, 2, 2, 20, 00),
                (2015, 2, 3, 20, 00),
                (2015, 2, 4, 20, 00),
            ],
            # \u2013 is an en dash!
            "Mon 2nd\u2013Wed 4th / 8pm",
        )

    def test_five_showings_non_seq_after_two(self):
        self._test_equiv(
            [
                (2015, 2, 2, 20, 00),
                (2015, 2, 3, 20, 00),
                (2015, 2, 5, 20, 00),
                (2015, 2, 6, 20, 00),
                (2015, 2, 7, 20, 00),
            ],
            "Mon 2nd, Tue 3rd, Thu 5th\u2013Sat 7th / 8pm",
        )

    def test_five_showings_non_seq_after_three(self):
        self._test_equiv(
            [
                (2015, 2, 2, 20, 00),
                (2015, 2, 3, 20, 00),
                (2015, 2, 4, 20, 00),
                (2015, 2, 6, 20, 00),
                (2015, 2, 7, 20, 00),
            ],
            "Mon 2nd\u2013Wed 4th, Fri 6th, Sat 7th / 8pm",
        )

    def test_complex(self):
        self._test_equiv(
            [
                (2015, 2, 1, 20, 00),
                (2015, 2, 2, 8, 00),
                (2015, 2, 2, 20, 00),
                (2015, 2, 3, 20, 00),
                (2015, 2, 4, 20, 00),
                (2015, 2, 5, 20, 00),
                (2015, 2, 17, 20, 00),
                (2015, 2, 18, 20, 00),
                (2015, 2, 20, 20, 00),
                (2015, 2, 21, 20, 00),
                (2015, 2, 23, 20, 00),
                (2015, 2, 24, 8, 15),
                (2015, 2, 28, 20, 00),
            ],
            "Sun 1st / 8pm, Mon 2nd / 8am, Mon 2nd\u2013Thu 5th, Tue 17th, "
            "Wed 18th, Fri 20th, Sat 21st, Mon 23rd / 8pm, Tue 24th / 8:15am,"
            " Sat 28th / 8pm",
        )

    def test_five_showings_seq_month_boundary(self):
        self._test_equiv(
            [
                (2015, 2, 26, 20, 00),
                (2015, 2, 27, 20, 00),
                (2015, 2, 28, 20, 00),
                (2015, 3, 1, 20, 00),
                (2015, 3, 2, 20, 00),
            ],
            "Thu 26th\u2013Sat 28th / 8pm, Sun 1st, Mon 2nd / 8pm",
        )
