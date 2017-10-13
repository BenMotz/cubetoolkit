from __future__ import absolute_import, unicode_literals
from datetime import timedelta

from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse

from toolkit.diary.models import RotaEntry, Showing

from .common import DiaryTestsMixin


class EditRotaViewGet(DiaryTestsMixin, TestCase):
    """Test that rota edit view loads"""

    def setUp(self):
        super(EditRotaViewGet, self).setUp()
        self.assertTrue(
            self.client.login(username="rota_editor",
                              password="T3stPassword!3")
        )

    def tearDown(self):
        self.client.logout()

    @patch('django.utils.timezone.now')
    def test_default_date_range(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("rota-edit")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_rota.html")

        # Check date range:
        self.assertContains(
            response,
            r'<input type="text" name="from_date" value="1-06-2013" '
            r'id="id_from_date" />',
            html=True
        )
        self.assertContains(
            response,
            r'<input type="text" name="to_date" value="1-07-2013" '
            r'id="id_to_date" />',
            html=True
        )

        # Check event listed:
        self.assertContains(
            response,
            '<a href="/programme/showing/id/7/">EVENT FOUR TITL\u0112</a>',
            html=True
        )

        # Notes present:
        self.assertContains(response, "Some notes about the Rota!")

    @patch('django.utils.timezone.now')
    def test_date_range(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("rota-edit")
        url = "{0}/{1}/{2:02}/{3:02}?daysahead=10".format(
            url,
            self._fake_now.year,
            self._fake_now.month,
            self._fake_now.day + 10,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_rota.html")

        # Check date range:
        self.assertContains(
            response,
            r'<input type="text" name="from_date" value="11-06-2013" '
            r'id="id_from_date" />',
            html=True
        )
        self.assertContains(
            response,
            r'<input type="text" name="to_date" value="21-06-2013" '
            r'id="id_to_date" />',
            html=True
        )

        # Check event not listed:
        self.assertNotContains(response, 'EVENT FOUR TITL\u0112')
        self.assertNotContains(response, "Some notes about the Rota!")


class EditRotaViewPost(DiaryTestsMixin, TestCase):
    """Test of rota edit posting"""

    def setUp(self):
        super(EditRotaViewPost, self).setUp()
        self.assertTrue(
            self.client.login(username="rota_editor",
                              password="T3stPassword!3")
        )

    def tearDown(self):
        self.client.logout()

    @patch('django.utils.timezone.now')
    def test_edit_entry(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("rota-edit")

        # Get data that will be edited:
        rota_entries = self.e4s3.rotaentry_set.all()
        self.assertEqual(len(rota_entries), 1)
        rota_entry = self.e4s3.rotaentry_set.all()[0]
        self.assertEqual(rota_entry.name, "")

        # New content
        entry = "\u01aeesty McTestingt\u01d2n III"

        response = self.client.post(url, data={
            'id': rota_entry.pk,
            'value': entry
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, entry.encode("utf-8"))

        # Check edit happened:
        rota_entry = RotaEntry.objects.get(pk=rota_entry.pk)
        self.assertEqual(rota_entry.name, entry)

    @patch('django.utils.timezone.now')
    def test_clear_entry(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("rota-edit")

        # Set data that will be cleared:
        rota_entries = self.e4s3.rotaentry_set.all()
        self.assertEqual(len(rota_entries), 1)
        rota_entry = self.e4s3.rotaentry_set.all()[0]
        rota_entry.name = "Not going to work!"
        rota_entry.save()

        # New content

        response = self.client.post(url, data={
            'id': rota_entry.pk,
            'value': ""
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

        # Check edit happened:
        rota_entry = RotaEntry.objects.get(pk=rota_entry.pk)

    @patch('django.utils.timezone.now')
    def test_edit_entry_in_past(self, now_patch):

        url = reverse("rota-edit")

        # Get data that will be edited:
        rota_entries = self.e4s3.rotaentry_set.all()
        self.assertEqual(len(rota_entries), 1)
        rota_entry = self.e4s3.rotaentry_set.all()[0]
        self.assertEqual(rota_entry.name, "")

        # Make sure time is after the event:
        now_patch.return_value = self.e4s3.start + timedelta(seconds=1)

        response = self.client.post(url, data={
            'id': rota_entry.pk,
            'value': "Spang",
        })

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode("utf-8"),
                         "Can't change rota for showings in the past")

        # Check edit didn't happen:
        rota_entry = RotaEntry.objects.get(pk=rota_entry.pk)
        self.assertEqual(rota_entry.name, "")

    def test_missing_name_and_id(self):
        url = reverse("rota-edit")
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode("utf-8"), "Invalid entry id")

    def test_missing_id(self):
        url = reverse("rota-edit")
        response = self.client.post(url, data={'name': "Whoops"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode("utf-8"), "Invalid entry id")

    @patch('django.utils.timezone.now')
    def test_missing_name(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("rota-edit")

        rota_entry = self.e4s3.rotaentry_set.all()[0]

        response = self.client.post(url, data={'id': rota_entry.pk})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode("utf-8"), "Invalid request")

    def test_unknown_id(self):
        url = reverse("rota-edit")
        response = self.client.post(url, data={
            'id': "1001",
            'value': "Foo!"
        })
        self.assertEqual(response.status_code, 404)

    def test_invalid_id(self):
        url = reverse("rota-edit")
        response = self.client.post(url, data={
            'id': "spanner",
            'value': "Foo!"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode("utf-8"), "Invalid entry id")


class EditRotaNotes(DiaryTestsMixin, TestCase):
    """Test of editing per-showing rota notes"""

    def setUp(self):
        super(EditRotaNotes, self).setUp()
        self.assertTrue(
            self.client.login(username="rota_editor",
                              password="T3stPassword!3")
        )

    def tearDown(self):
        self.client.logout()

    @patch('django.utils.timezone.now')
    def test_get_forbidden(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing-rota-notes",
                      kwargs={"showing_id": self.e4s3.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    @patch('django.utils.timezone.now')
    def test_post(self, now_patch):
        now_patch.return_value = self._fake_now

        new_notes = "Line 1\nLine 2\n ...etc. (\u01d4\u01cbcode!)"

        url = reverse("edit-showing-rota-notes",
                      kwargs={"showing_id": self.e4s3.pk})

        response = self.client.post(url, data={
            "rota_notes": new_notes,
        })
        self.assertEqual(response.status_code, 200)

        showing = Showing.objects.get(pk=self.e4s3.pk)
        self.assertEqual(showing.rota_notes, new_notes)

    @patch('django.utils.timezone.now')
    def test_edit_past_showing_fails(self, now_patch):
        now_patch.return_value = self.e4s3.start + timedelta(seconds=1)

        original_notes = self.e4s3.rota_notes

        url = reverse("edit-showing-rota-notes",
                      kwargs={"showing_id": self.e4s3.pk})

        response = self.client.post(url, data={
            "rota_notes": "Nope",
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode("utf-8"),
                         "Can't change rota for showings in the past")

        showing = Showing.objects.get(pk=self.e4s3.pk)
        self.assertEqual(showing.rota_notes, original_notes)

    @patch('django.utils.timezone.now')
    def test_post_clear_notes(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing-rota-notes",
                      kwargs={"showing_id": self.e4s3.pk})

        response = self.client.post(url, data={
            'rota_notes': ""
        })
        self.assertEqual(response.status_code, 200)

        showing = Showing.objects.get(pk=self.e4s3.pk)
        self.assertEqual(showing.rota_notes, "")

    @patch('django.utils.timezone.now')
    def test_post_clear_notes_no_data(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing-rota-notes",
                      kwargs={"showing_id": self.e4s3.pk})

        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 200)

        showing = Showing.objects.get(pk=self.e4s3.pk)
        self.assertEqual(showing.rota_notes, "")
