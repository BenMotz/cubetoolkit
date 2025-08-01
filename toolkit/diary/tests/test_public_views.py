from datetime import datetime, timedelta
import zoneinfo

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse, resolve
import django.http

from .common import DiaryTestsMixin

uktz = zoneinfo.ZoneInfo("Europe/London")


class PublicDiaryViews(DiaryTestsMixin, TestCase):
    """Basic test that all the public diary pages load"""

    def test_view_default(self):
        # Hard code root URL to assert that it gets something:
        response = self.client.get("/programme/")
        self.assertEqual(response.status_code, 200)

    def test_view_default_reversed(self):
        url = reverse("default-view")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")

    @patch("django.utils.timezone.now")
    def test_view_empty_slug(self, now_patch):
        # When an event has a name that results in a slugified event name of
        # ""
        now_patch.return_value = datetime(2013, 4, 1, 11, 00, tzinfo=uktz)

        self.e2.name = "?"
        self.e2.save()

        url = reverse("default-view")
        response = self.client.get(url)

        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            r'<a href="/programme/event/,2/">'
            r'<p><span class="pre_title"></span></p>'
            r"<h3>?</h3>"
            r'<span class="post_title"></span>'
            r"</a>",
            html=True,
        )

    def test_view_by_type(self):
        url = reverse("type-view", kwargs={"event_type": "film"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")

    def test_view_by_year(self):
        url = reverse("year-view", kwargs={"year": "2013"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")

        # Should test the contents better, I suspect...
        self.assertContains(response, "Event three title")
        self.assertContains(response, "Copy three summary")
        self.assertContains(response, "PRETITLE THREE")
        self.assertContains(response, "POSTTITLE THREE")
        # Not confirmed / private:
        self.assertNotContains(response, "Event one title")
        self.assertNotContains(response, "Event one copy")

    def test_view_by_month(self):
        url = reverse("month-view", kwargs={"year": "2010", "month": "12"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")

    def test_view_by_day(self):
        url = reverse(
            "day-view", kwargs={"year": "2010", "month": "12", "day": "31"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")

    def test_view_by_tag_nothing_found(self):
        url = reverse("type-view", kwargs={"event_type": "folm"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertContains(
            response,
            '<h4 class="site-description">Folm events</h4>',
            html=True,
        )
        self.assertContains(
            response,
            '<h4 class="site-description"> - couldn\'t find '
            "anything tagged folm </h4>",
            html=True,
        )

    def test_view_by_date_nothing_found(self):
        url = reverse("year-view", kwargs={"year": "2093"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertContains(
            response,
            '<h4 class="site-description">Nothing on between Thursday 1 Jan '
            "2093 and Friday 1 Jan 2094</h4>",
            html=True,
        )

    @patch("django.utils.timezone.now")
    def test_view_this_week(self, now_patch):
        now_patch.return_value = datetime(2013, 4, 1, 11, 00, tzinfo=uktz)

        url = reverse("view-this-week")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wed 3 April // 19:00")

    @patch("django.utils.timezone.now")
    def test_view_this_month(self, now_patch):
        now_patch.return_value = datetime(2013, 4, 1, 11, 00, tzinfo=uktz)

        url = reverse("view-this-month")
        response = self.client.get(url)

        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event two title")
        self.assertContains(
            response,
            '<span class="cancelled">Wed 3 April // 19:00</span>',
            html=True,
        )
        self.assertContains(response, "Event two copy summary")

    @patch("django.utils.timezone.now")
    def test_view_next_week(self, now_patch):
        now_patch.return_value = datetime(2013, 4, 1, 11, 00, tzinfo=uktz)

        url = reverse("view-next-week")
        response = self.client.get(url)

        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PRETITLE THREE")
        self.assertContains(response, "Event three title")
        self.assertContains(response, "POSTTITLE THREE")
        self.assertContains(response, "Sat 13 April // 18:00")
        self.assertContains(response, "Copy three summary")

    @patch("django.utils.timezone.now")
    def test_view_next_month(self, now_patch):
        now_patch.return_value = datetime(2013, 3, 1, 11, 00, tzinfo=uktz)

        url = reverse("view-next-month")
        response = self.client.get(url)

        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PRETITLE THREE")
        self.assertContains(response, "Event three title")
        self.assertContains(response, "POSTTITLE THREE")
        self.assertContains(response, "Sat 13 April // 18:00")
        self.assertContains(response, "Copy three summary")

    # View of individual showing:
    def test_view_showing(self):
        url = reverse(
            "single-showing-view", kwargs={"showing_id": str(self.e2s2.pk)}
        )
        response = self.client.get(url)
        self.assertContains(response, "Event two title")
        self.assertContains(response, "Event <br>\n two <br>\n copy")
        self.assertEqual(response.status_code, 200)

    def test_view_hidden_showing(self):
        url = reverse(
            "single-showing-view", kwargs={"showing_id": str(self.e2s1.pk)}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # Event series view:
    @patch("django.utils.timezone.now")
    def test_view_event_this_year(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("single-event-view", kwargs={"event_id": "2"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_event.html")

        # TODO: test data better, including media!
        self.assertContains(response, "Event two title")
        self.assertContains(response, "Event <br>\n two <br>\n copy")
        self.assertEqual(response.status_code, 200)
        # Some showings *should* be listed:
        self.assertContains(response, "Tue 2 April // 19:00")
        self.assertContains(response, "Wed 3 April // 19:00")
        # Some showings should *not* be listed:
        self.assertNotContains(response, "1 Apr")
        self.assertNotContains(response, "4 Apr")
        self.assertNotContains(response, "5 Apr")

    @patch("django.utils.timezone.now")
    def test_view_event_last_year(self, now_patch):
        # When event is in the distant past, list the year...
        now_patch.return_value = self._fake_now + timedelta(days=366)

        url = reverse("single-event-view", kwargs={"event_id": "2"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_event.html")

        self.assertContains(response, "Event two title")
        self.assertContains(response, "Event <br>\n two <br>\n copy")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tue 2 April 2013 // 19:00")
        self.assertContains(response, "Wed 3 April 2013 // 19:00")
        self.assertNotContains(response, "1 Apr")
        self.assertNotContains(response, "4 Apr")
        self.assertNotContains(response, "5 Apr")

    def test_view_event_legacy(self):
        url = reverse(
            "single-event-view-legacyid", kwargs={"legacy_id": "100"}
        )
        response = self.client.get(url)
        # TODO: test data!
        self.assertEqual(response.status_code, 200)

    def test_view_event_no_public_showings(self):
        # Event 1 has no publicly viewable showings:
        url = reverse("single-event-view", kwargs={"event_id": "1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def _assert_ticket_link_present(self, event_id, ticket_link):
        url = reverse("single-event-view", kwargs={"event_id": str(event_id)})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_event.html")
        self.assertContains(
            response,
            '<a href="{0}"  rel="noopener noreferrer" target="_blank">'
            "Book tickets</a>".format(ticket_link),
            html=True,
        )

    @patch("django.utils.timezone.now")
    def test_view_event_buy_ticket_link(self, now_patch):
        # Time is before any showings have started
        first_public_showing = self.e2.showings.public()[0]
        now_patch.return_value = first_public_showing.start - timedelta(
            seconds=1
        )
        ticket_link = "http://www.example.com/thing/#what"
        self.e2.ticket_link = ticket_link
        self.e2.save()
        self._assert_ticket_link_present(self.e2.pk, ticket_link)

    @patch("django.utils.timezone.now")
    def test_view_event_buy_ticket_link_some_showings_finished(
        self, now_patch
    ):
        # Time is before last showings has started
        last_public_showing = list(self.e2.showings.public())[-1]
        now_patch.return_value = last_public_showing.start - timedelta(
            seconds=1
        )
        ticket_link = "http://www.example.com/goo/#what"
        self.e2.ticket_link = ticket_link
        self.e2.save()
        self._assert_ticket_link_present(self.e2.pk, ticket_link)

    @patch("django.utils.timezone.now")
    def test_view_event_buy_ticket_link_finished_event(self, now_patch):
        # Book ticket link should not be visible after all showings are
        # complete
        last_public_showing = list(self.e2.showings.public())[-1]
        now_patch.return_value = last_public_showing.start + timedelta(
            seconds=1
        )
        ticket_link = "http://www.example.com/thing/#what"
        self.e2.ticket_link = ticket_link
        self.e2.save()

        url = reverse("single-event-view", kwargs={"event_id": "2"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_event.html")
        self.assertNotContains(response, "Book tickets")
        self.assertNotContains(response, ticket_link)

    def test_expected_tags_in_navmenu(self):
        url = reverse("default-view")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "view_showing_index.html")
        self.assertEqual(response.status_code, 200)
        # Note that tags are title-cased in response, and ordering is
        # significant!
        self.assertContains(
            response,
            '<ul class="sub-menu">'
            '<li><a href="/programme/view/tag-three/"><span>Tag Three</span></a></li>'
            '<li><a href="/programme/view/tag-two/"><span>Tag Two</span></a></li>'
            '<li><a href="/programme/"><span>All</span></a></li>'
            '<li><a href="/programme/archive/"><span>Archive</span></a></li>'
            "</ul>",
            html=True,
        )

    # TODO: Cancelled/confirmed/visible/cheap


class UrlTests(DiaryTestsMixin, TestCase):
    """Test the regular expressions in urls.py"""

    def test_diary_urls(self):
        # Test all basic diary URLs
        calls_to_test = {
            # '/diary': (), # This is a 302...
            "/programme/view/": {},
            "/programme/view/2012": {"year": "2012"},
            "/programme/view/2012/": {"year": "2012"},
            "/programme/view/2012/12": {"year": "2012", "month": "12"},
            "/programme/view/2012/12/": {"year": "2012", "month": "12"},
            "/programme/view/2012/12/30": {
                "year": "2012",
                "month": "12",
                "day": "30",
            },
            "/programme/view/2012/12/30/": {
                "year": "2012",
                "month": "12",
                "day": "30",
            },
            "/programme/view/films/": {"event_type": "films"},
            # Tags that are similar to, but aren't quite the same as, years:
            "/programme/view/1/": {"event_type": "1"},
            "/programme/view/12/": {"event_type": "12"},
            "/programme/view/123/": {"event_type": "123"},
            "/programme/view/12345/": {"event_type": "12345"},
        }
        for query, response in calls_to_test.items():
            match = resolve(query)
            self.assertEqual(match.func.__name__, "view_diary")
            for k, v in response.items():
                self.assertEqual(match.kwargs[k], v)

    def test_diary_invalid_urls(self):
        # Test all basic diary URLs

        calls_to_test = (
            "/diary/123",
            "/diary/-123",
            "/diary/-2012/",
            "/diary/2012//",
            "/diary/2012///",
        )
        for query in calls_to_test:
            self.assertRaises(django.http.Http404, resolve, query)

    def test_diary_edit_urls(self):
        # Test all basic diary URLs

        calls_to_test = {
            "/diary/edit": {},
            "/diary/edit/": {},
            "/diary/edit/2012": {"year": "2012"},
            "/diary/edit/2012/": {"year": "2012"},
            "/diary/edit/2012/12": {"year": "2012", "month": "12"},
            "/diary/edit/2012/12/": {"year": "2012", "month": "12"},
            "/diary/edit/2012/12/30": {
                "year": "2012",
                "month": "12",
                "day": "30",
            },
            "/diary/edit/2012/12/30/": {
                "year": "2012",
                "month": "12",
                "day": "30",
            },
        }
        for query, response in calls_to_test.items():
            match = resolve(query)
            self.assertEqual(match.func.__name__, "edit_diary_list")
            for k, v in response.items():
                self.assertEqual(match.kwargs[k], v)

    def test_diary_rota_urls(self):
        # Test all basic diary URLs

        calls_to_test = {
            "/diary/rota": {"field": "rota"},
            "/diary/rota/": {"field": "rota"},
            "/diary/rota/2012/12": {
                "field": "rota",
                "year": "2012",
                "month": "12",
            },
            "/diary/rota/2012/12/": {
                "field": "rota",
                "year": "2012",
                "month": "12",
            },
            "/diary/rota/2012/12/30": {
                "field": "rota",
                "year": "2012",
                "month": "12",
                "day": "30",
            },
            "/diary/rota/2012/12/30/": {
                "field": "rota",
                "year": "2012",
                "month": "12",
                "day": "30",
            },
            "/diary/rota/2012/12//": {
                "field": "rota",
                "year": "2012",
                "month": "12",
                "day": "",
            },
        }
        # (rota URLS must have at least year/month, not just a year!)
        for query, response in calls_to_test.items():
            match = resolve(query)
            self.assertEqual(match.func.__name__, "view_event_field")
            for k, v in response.items():
                self.assertEqual(match.kwargs[k], v)
