from __future__ import absolute_import

import datetime
import urllib
import xml.etree.ElementTree as ElementTree

from mock import patch

from django.test import TestCase
from django.urls import reverse

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

    def test_feed_title(self):
        tree = self._get_etree()
        self.assertEqual(
            tree.find("channel").find("title").text,
            "Cube cinema forthcoming events",
        )

    def test_feed_link(self):
        tree = self._get_etree()
        link_text = tree.find("channel").find("link").text
        link_parts = urllib.parse.urlparse(link_text)
        self.assertEqual(link_parts.path, "/programme")

    @patch("django.utils.timezone.now")
    def test_feed_items(self, now_patch):
        # Feed should only have 7 days in advance, so fiddle the mock time to
        # bring the fake now into range of the one qualifying showing:
        now_patch.return_value = self._fake_now + datetime.timedelta(days=5)
        tree = self._get_etree()
        # expect event 4 / showing 3:
        items = tree.find("channel").findall("item")
        self.assertEqual(len(items), 1)
        item = items[0]

        showing = self.e4s3

        self.assertEqual(item.find("title").text, u"Event four titl\u0113")
        self.assertEqual(
            item.find("description").text,
            u"09/06/2013 17:00<br><br>Event four C\u014dpy",
        )
        item_link_path = urllib.parse.urlparse(item.find("link").text).path
        self.assertEqual(
            item_link_path,
            reverse(
                "single-event-view", kwargs={"event_id": showing.event_id}
            ),
        )
        # Guid should be the same as the link:
        self.assertEqual(item.find("link").text, item.find("guid").text)

    @patch("django.utils.timezone.now")
    def test_feed_no_items(self, now_patch):
        # Feed should only have 7 days in advance, this time will yield
        # nothing:
        now_patch.return_value = self._fake_now
        tree = self._get_etree()
        items = tree.find("channel").findall("item")
        self.assertEqual(len(items), 0)
