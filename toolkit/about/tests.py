from __future__ import absolute_import

from django.test import TestCase


class AboutViewTests(TestCase):

    """Basic test that all the about pages load"""

    def test_urls(self):
        urls = [
            "/about/",
            "/about/directions/",
            "/about/membership/",
            "/about/contact/",
            "/about/newsletter/",
            "/about/tickets/",
            "/about/images/",
            "/about/tech/",
            "/about/hire/",
            "/about/volunteer/",
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            # No trailing slash should 301 redirect:
            response = self.client.get(url[:-1])
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response['Location'],
                             "http://testserver%s" % url)
