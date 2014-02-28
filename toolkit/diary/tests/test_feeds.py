from __future__ import absolute_import

import urlparse
import xml.etree.ElementTree as ElementTree

from django.test import TestCase
from django.core.urlresolvers import reverse

from .common import DiaryTestsMixin


class FeedTests(DiaryTestsMixin, TestCase):
    """Basic test that RSS feed loads and has expected content"""

    def test_feed_loads(self):
        url = reverse("view-diary-rss")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_feed_loads_and_parses(self):
        url = reverse("view-diary-rss")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Will raise an exception if it can't parse XML:
        ElementTree.fromstring(response.content)

    def _get_etree(self):
        url = reverse("view-diary-rss")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return ElementTree.fromstring(response.content)

    def test_feed_link(self):
        tree = self._get_etree()
        link_text = tree.find('channel').find('link').text
        link_parts = urlparse.urlparse(link_text)
        self.assertEqual(link_parts.path, "/programme")
