from __future__ import absolute_import

from django.test import TestCase
from django.template import Context, Template
from django.urls import get_script_prefix, set_script_prefix


class TestNoPrefixURLTag(TestCase):
    def setUp(self):
        self._initial_prefix = get_script_prefix()

    def tearDown(self):
        set_script_prefix(self._initial_prefix)

    def test_prefixes(self):
        prefixes = ["/gibbarish/", "/c/", "", "/X/"]
        for prefix in prefixes:
            set_script_prefix(prefix)
            out = Template(
                "{% load noprefix_url %}"
                "Chicken sandwich: "
                "{% noprefix_url 'day-view' '2015' '01' '01' %}"
            ).render(Context())
            self.assertEqual(
                out, "Chicken sandwich: /programme/view/2015/01/01"
            )
