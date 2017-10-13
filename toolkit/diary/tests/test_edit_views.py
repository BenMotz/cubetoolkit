from __future__ import absolute_import, unicode_literals
import re
import json
import os.path

import six
import pytz
from datetime import datetime, date, time
import tempfile
import six.moves

from mock import patch

from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
import six

from toolkit.diary.models import (Showing, Event, Role, DiaryIdea,
                                  EventTemplate, MediaItem, EventTag)
import toolkit.diary.edit_prefs

from .common import DiaryTestsMixin

TINY_VALID_PNG = bytearray(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08'
    b'\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00'
    b'\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00\tpHYs\x00\x00'
    b'\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x0cIDAT\x18Wc\xf8\xff'
    b'\xff?\x00\x05\xfe\x02\xfe\xa75\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82')

TINY_VALID_JPEG = bytearray(
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x02\x00&\x00&\x00\x00\xff'
    b'\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03'
    b'\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t'
    b'\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10'
    b'\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc0\x00\x0b\x08\x00'
    b'\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\xff\xc4\x00\x14\x10'
    b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00T\xdf\xff\xd9')


class ViewSecurity(DiaryTestsMixin, TestCase):

    """Basic test that the private diary pages require the correct
    permissions"""

    write_required = {
        "edit-event-details": {"event_id": "1"},
        "edit-showing": {"showing_id": "1"},
        "edit-ideas": {"year": "2012", "month": "1"},
        "add-showing": {"event_id": "1"},
        "delete-showing": {"showing_id": "1"},
        "add-event": {},

        "edit_event_templates": {},
        "edit_event_tags": {},
        "edit_roles": {},
        "members-mailout": {},
        "exec-mailout": {},
        "mailout-progress": {},
        "mailout-test-send": {},

        "add-printed-programme": {},
    }

    only_read_required = {
        "default-edit": {},
        "diary-edit-calendar": {},
        "edit-diary-data": {},
        "year-edit": {"year": "2013"},
        "month-edit": {"year": "2013", "month": "1"},
        "day-edit": {"year": "2013", "month": "1", "day": "1"},
        "edit-event-details-view": {"pk": "1"},
        "cancel-edit": {},
        "view_event_field": {"field": "rota"},

        "set_edit_preferences": {},

        "edit-printed-programmes": {},
    }

    rota_edit_required = {
        "rota-edit": {},
        "edit-showing-rota-notes": {"showing_id": "1"},
        "view-rota-vacancies": {},
    }

    def _assert_need_login(self, views_to_test):
        for view_name, kwargs in six.iteritems(views_to_test):
            url = reverse(view_name, kwargs=kwargs)
            expected_redirect = ("{0}?next={1}".format(
                reverse("login"), url))
            # Test GET:
            response = self.client.get(url)
            self.assertRedirects(response, expected_redirect)
            # Test POST:
            response = self.client.post(url)
            self.assertRedirects(response, expected_redirect)

    def test_need_login(self):
        """
        Checks all URLs that shouldn't work when not logged in at all
        """
        views_to_test = {}
        views_to_test.update(self.write_required)
        views_to_test.update(self.only_read_required)
        views_to_test.update(self.rota_edit_required)

        self._assert_need_login(views_to_test)

    def test_need_write(self):
        """
        Checks all URLs that shouldn't work when logged in user doesn't have
        'toolkit.write' permission
        """
        # login as read only user:
        self.client.login(username="read_only", password="T3stPassword!1")

        views_to_test = {}
        views_to_test.update(self.write_required)
        views_to_test.update(self.rota_edit_required)

        self._assert_need_login(views_to_test)

    def test_need_read_or_write(self):
        """
        Checks all URLs that shouldn't work when logged in user doesn't have
        'toolkit.write' or 'toolkit.read' permission
        """
        views_to_test = {}
        views_to_test.update(self.write_required)
        views_to_test.update(self.only_read_required)
        views_to_test.update(self.rota_edit_required)

        # login as no permission user:
        self.client.login(username="no_perm", password="T3stPassword!2")

        self._assert_need_login(views_to_test)

    def test_rota_editor_no_access(self):
        """
        Checks all URLs that shouldn't work when logged in user doesn't have
        'toolkit.write' or 'toolkit.read' permission
        """
        views_to_test = {}
        views_to_test.update(self.write_required)
        views_to_test.update(self.only_read_required)
        # i.e. everything except self.rota_edit_required

        # login as rota editing permission user:
        self.client.login(username="rota_editor", password="T3stPassword!3")

        self._assert_need_login(views_to_test)


class EditDiaryViews(DiaryTestsMixin, TestCase):

    """Basic test that various private diary pages load"""

    def setUp(self):
        super(EditDiaryViews, self).setUp()

        self.client.login(username="admin", password="T3stPassword!")

    def tearDown(self):
        self.client.logout()

    def test_view_default(self):
        url = reverse("default-edit")
        response = self.client.get(url)
        # self.assertIn(u'Event one title', response.content)
        # self.assertIn(u'<p>Event one copy</p>', response.content)
        self.assertEqual(response.status_code, 200)

    def test_view_calendar(self):
        url = reverse("diary-edit-calendar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_event_calendar_index.html")

    def test_view_tag_editor(self):
        url = reverse("edit_event_tags")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_event_tags.html")

    def test_view_template_editor(self):
        url = reverse("edit_event_templates")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_event_templates.html")

    def test_view_role_editor(self):
        url = reverse("edit_roles")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_edit_roles.html")


class AddShowingView(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(AddShowingView, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def test_add_showing_must_post(self):
        # Add a new showing
        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"
        # TODO: Add more query data that might work
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)

    @patch('django.utils.timezone.now')
    def test_add_showing_mismatching_event_id(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("add-showing", kwargs={"event_id": 1})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 5)

        # do add/clone:
        response = self.client.post(url, data={
            "booked_by": "Someone or the other - \u20ac",
            "clone_start": "13/07/2013 20:00"
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertEqual(response.status_code, 404)

    def test_add_showing_no_copy_from(self):
        # No copy_from parameter: should return 404
        url = reverse("add-showing", kwargs={"event_id": 1})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_add_showing_no_start(self):
        url = reverse("add-showing", kwargs={"event_id": 2})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 5)

        response = self.client.post(url, data={
            "booked_by": "someone",
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertFormError(response, 'clone_showing_form', 'clone_start',
                             'This field is required.')

    def test_add_showing_no_booked_by(self):
        url = reverse("add-showing", kwargs={"event_id": 2})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 5)

        # Start is in past, but should get error about missing booked_by
        response = self.client.post(url, data={
            "clone_start": "13/07/2010 20:00"
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertFormError(response, 'clone_showing_form', 'booked_by',
                             'This field is required.')

    @patch('django.utils.timezone.now')
    def test_add_showing_in_past(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("add-showing", kwargs={"event_id": 2})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 5)

        # do add/clone:
        response = self.client.post(url, data={
            "booked_by": "Someone",
            "clone_start": "01/01/2010 20:00"  # The past!
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before)

        self.assertFormError(response, 'clone_showing_form', 'clone_start',
                             'Must be in the future')

    @patch('django.utils.timezone.now')
    def test_add_showing(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("add-showing", kwargs={"event_id": 2})
        url += "?copy_from=2"

        showing_count_before = Showing.objects.count()

        source = Showing.objects.get(id=2)

        self.assertEqual(source.event.showings.count(), 5)

        # do add/clone:
        response = self.client.post(url, data={
            "booked_by": "Someone or the other - \u20ac",
            "clone_start": "13/07/2013 20:00"
        })

        showing_count_after = Showing.objects.count()
        self.assertEqual(showing_count_after, showing_count_before + 1)

        # Get clone:
        dest = list(source.event.showings.all())[-1]

        # Check "booked by":
        self.assertEqual(dest.booked_by, "Someone or the other - \u20ac")

        # Check fields were cloned:
        self.assertEqual(source.event_id, dest.event_id)
        self.assertEqual(source.extra_copy, dest.extra_copy)
        self.assertEqual(source.extra_copy_summary, dest.extra_copy_summary)
        self.assertEqual(source.confirmed, dest.confirmed)
        self.assertEqual(source.hide_in_programme, dest.hide_in_programme)
        self.assertEqual(source.cancelled, dest.cancelled)
        self.assertEqual(source.discounted, dest.discounted)

        # Check rota cloned:
        src_rota = source.rotaentry_set.all()
        dst_rota = dest.rotaentry_set.all()

        self.assertEqual(
            len(src_rota),
            len(dst_rota)
        )

        for src_entry, dst_entry in zip(source.rotaentry_set.all(),
                                        dest.rotaentry_set.all()):
            self.assertEqual(src_entry.role, dst_entry.role)
            self.assertEqual(src_entry.rank, dst_entry.rank)

        self.assert_return_to_index(response)


class EditShowing(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(EditShowing, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def tests_edit_showing_get(self):
        showing = Showing.objects.get(pk=7)

        url = reverse("edit-showing", kwargs={"showing_id": 7})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_showing.html")

        # (In the following, can't use "HTML" matching (which doesn't mind if
        # the text isn't exact, so long as it's equivalent) as the output isn't
        # currently valid HTML. Whoops.)

        # "clone" part should have expected start time:
        self.assertContains(
            response,
            '<input id="id_clone_start" name="clone_start" type="text"'
            ' value="10/06/2013 18:00" />'
        )
        # Edit should have existing values:
        self.assertContains(
            response,
            '<input id="id_start" name="start" type="text" '
            'value="09/06/2013 18:00" />'
        )
        self.assertContains(
            response,
            '<input id="id_booked_by" maxlength="64" name="booked_by" '
            'type="text" value="\u0102nother \u0170ser" />'
        )
        self.assertContains(
            response,
            '<input checked="checked" id="id_confirmed" name="confirmed" '
            'type="checkbox" />'
        )
        self.assertContains(
            response,
            '<input id="id_hide_in_programme" name="hide_in_programme" '
            'type="checkbox" />'
        )
        self.assertContains(
            response,
            '<input id="id_cancelled" name="cancelled" type="checkbox" />'
        )
        self.assertContains(
            response,
            '<input id="id_discounted" name="discounted" type="checkbox" />'
        )

        # Shouldn't contain excluded fields:
        self.assertNotContains(response, showing.rota_notes)

        # Rota edit:
        self.assertContains(
            response,
            '<input class="rota_count" id="id_role_1" name="role_1" '
            'type="text" value="0" />'
        )
        self.assertContains(
            response,
            '<option value="2" selected="selected">'
        )
        self.assertContains(
            response,
            '<option value="3">'
        )

    def _test_edit_showing_common(self, now_patch, multiroom_enabled):
        # Common code from the following two tests
        # Reload the forms module, to force handling of the MULTIROOM_ENABLED
        # conditional in the form definition (if required)
        six.moves.reload_module(toolkit.diary.forms)

        now_patch.return_value = self._fake_now

        url = reverse("edit-showing", kwargs={"showing_id": 7})
        response = self.client.post(url, data={
            "start": "15/08/2013 19:30",
            "booked_by": "Yet \u0102nother \u0170ser",
            "confirmed": "on",
            "hide_in_programme": "on",
            "cancelled": "on",
            "discounted": "on",
            "role_1": "3",
            "other_roles": "3",
            # data should be ignored if multiroom_enabled == False, but not
            # cause an error
            "room": "2",
        })

        self.assertEqual(response.status_code, 200)
        self.assert_return_to_index(response)

        # Check showing was updated:
        showing = Showing.objects.get(id=7)
        self.assertEqual(showing.start, pytz.utc.localize(
            datetime(2013, 8, 15, 18, 30)))
        self.assertEqual(showing.booked_by, "Yet \u0102nother \u0170ser")
        self.assertEqual(showing.confirmed, True)
        self.assertEqual(showing.hide_in_programme, True)
        self.assertEqual(showing.cancelled, True)
        self.assertEqual(showing.discounted, True)
        self.assertEqual(showing.room_id, 2 if multiroom_enabled else None)
        # Check rota is as expected:
        rota = list(showing.rotaentry_set.all())
        self.assertEqual(len(rota), 4)
        self.assertEqual(rota[0].role_id, 1)
        self.assertEqual(rota[0].rank, 1)
        self.assertEqual(rota[1].role_id, 1)
        self.assertEqual(rota[1].rank, 2)
        self.assertEqual(rota[2].role_id, 1)
        self.assertEqual(rota[2].rank, 3)
        self.assertEqual(rota[3].role_id, 3)
        self.assertEqual(rota[3].rank, 1)

    @override_settings(MULTIROOM_ENABLED=False)
    @patch('django.utils.timezone.now')
    def tests_edit_showing(self, now_patch):
        self._test_edit_showing_common(now_patch, False)

    @override_settings(MULTIROOM_ENABLED=True)
    @patch('django.utils.timezone.now')
    def tests_edit_showing_multiroom_enabled(self, now_patch):
        self._test_edit_showing_common(now_patch, True)

    @patch('django.utils.timezone.now')
    def tests_edit_showing_in_past(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing", kwargs={"showing_id": 1})
        response = self.client.post(url, data={
            "start": "15/08/2013 19:30",
            "booked_by": "Valid",
            "role_1": "0",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_showing.html")
        self.assert_has_message(
            response, "Can&#39;t edit showings that are in the past", "error")

    @patch('django.utils.timezone.now')
    def tests_edit_showing_missing_data(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing", kwargs={"showing_id": 3})
        response = self.client.post(url, data={
            "start": "",
            "booked_by": "",
            "role_1": "0",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_showing.html")

        self.assertFormError(response, 'form', 'start',
                             'This field is required.')
        self.assertFormError(response, 'form', 'booked_by',
                             'This field is required.')

    @patch('django.utils.timezone.now')
    def tests_edit_showing_invalid_date_past(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing", kwargs={"showing_id": 3})
        response = self.client.post(url, data={
            "start": "15/01/2013 19:30",
            "booked_by": "Valid",
            "role_1": "0",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_showing.html")

        self.assertFormError(response, 'form', 'start',
                             'Must be in the future')

    @patch('django.utils.timezone.now')
    def tests_edit_showing_invalid_date_malformed(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("edit-showing", kwargs={"showing_id": 3})
        response = self.client.post(url, data={
            "start": "Spinach",
            "booked_by": "Valid",
            "role_1": "0",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_showing.html")

        self.assertFormError(response, 'form', 'start',
                             'Enter a valid date/time.')


class DeleteShowing(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(DeleteShowing, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def test_delete_showing_must_post(self):

        url = reverse("delete-showing", kwargs={"showing_id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Will raise an exception if it doesn't exist
        Showing.objects.get(id=1)

    @patch('django.utils.timezone.now')
    def test_delete_showing_in_past(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("delete-showing", kwargs={"showing_id": 1})
        response = self.client.post(url)

        # Should redirect to edit page:
        self.assertRedirects(response, reverse(
            "edit-showing", kwargs={"showing_id": 1}))

        # Showing should still exist:
        # Will raise an exception if it doesn't exist
        Showing.objects.get(id=1)

    @patch('django.utils.timezone.now')
    def test_delete_showing(self, now_patch):
        now_patch.return_value = self._fake_now

        self.assertTrue(Showing.objects.filter(id=7))

        url = reverse("delete-showing", kwargs={"showing_id": 7})
        response = self.client.post(url)

        # Showing should have been deleted
        self.assertFalse(Showing.objects.filter(id=7))

        self.assert_return_to_index(response)


class AddEventView(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(AddEventView, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def tearDown(self):
        # Reload the forms module, to revert any forced handling of the
        # MULTIROOM_ENABLED conditional
        six.moves.reload_module(toolkit.diary.forms)

    @patch('django.utils.timezone.now')
    def test_get_add_event_form_default_start(self, now_patch):
        now_patch.return_value = self._fake_now

        url = reverse("add-event")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_event_and_showing.html")
        # Default start should be set one day in the future:
        self.assertContains(
            response,
            r'<input id="id_start" name="start" value="02/06/2013 20:00" '
            r'type="text" />',
            html=True
        )

    def test_get_add_event_form_specify_start(self):
        url = reverse("add-event")
        response = self.client.get(url, data={"date": "01-01-1950"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_event_and_showing.html")
        # Default start should be set one day in the future:
        self.assertContains(
            response,
            r'<input id="id_start" name="start" value="01/01/1950 20:00" '
            r'type="text" />',
            html=True
        )

    def test_get_add_event_form_specify_malformed_start(self):
        url = reverse("add-event")
        response = self.client.get(url, data={"date": "crisp packet"})
        self.assertContains(response, "Invalid start date", status_code=400)

    def test_get_add_event_form_specify_invalid_start(self):
        url = reverse("add-event")
        response = self.client.get(url, data={"date": "99-01-1950"})
        self.assertContains(
            response, "Illegal time, date, duration or room", status_code=400)

    # Common code for the following two tests::w
    def _test_add_event_common(self, now_patch, multiroom_enabled):
        # Reload the forms module, to force handling of the MULTIROOM_ENABLED
        # conditional in the form definition (if required)
        six.moves.reload_module(toolkit.diary.forms)
        now_patch.return_value = self._fake_now

        url = reverse("add-event")
        response = self.client.post(url, data={
            "start": "02/06/2013 20:00",
            "duration": "01:30:00",
            "number_of_days": "3",
            "event_name": "Ev\u0119nt of choic\u0119",
            "event_template": "1",
            "booked_by": "\u015Comeb\u014ddy",
            "private": "on",
            "outside_hire": "",
            "confirmed": "on",
            "discounted": "on",
            "room": "2",
        })
        # Request succeeded?
        self.assertEqual(response.status_code, 200)
        self.assert_return_to_index(response)

        # Event added correctly?
        event = Event.objects.get(name="Ev\u0119nt of choic\u0119")
        self.assertEqual(event.duration, time(1, 30))
        self.assertEqual(event.private, True)
        self.assertEqual(event.outside_hire, False)
        self.assertEqual(event.template, EventTemplate.objects.get(id=1))

        showings = list(event.showings.all())
        self.assertEqual(len(showings), 3)
        # Showings should have been added over 3 days. Time specified was BST,
        # so should be 7pm in UTC:
        self.assertEqual(showings[0].start, pytz.utc.localize(
            datetime(2013, 6, 2, 19, 0)))
        self.assertEqual(showings[1].start, pytz.utc.localize(
            datetime(2013, 6, 3, 19, 0)))
        self.assertEqual(showings[2].start, pytz.utc.localize(
            datetime(2013, 6, 4, 19, 0)))

        role_1 = Role.objects.get(id=1)
        for s in showings:
            self.assertEqual(s.booked_by, "\u015Comeb\u014ddy")
            self.assertEqual(s.confirmed, True)
            self.assertEqual(s.hide_in_programme, False)
            self.assertEqual(s.cancelled, False)
            self.assertEqual(s.discounted, True)
            self.assertEqual(list(s.roles.all()), [role_1, ])
            self.assertEqual(s.room_id, 2 if multiroom_enabled else None)

    @override_settings(MULTIROOM_ENABLED=False)
    @patch('django.utils.timezone.now')
    def test_add_event(self, now_patch):
        self._test_add_event_common(now_patch, False)

    @override_settings(MULTIROOM_ENABLED=True)
    @patch('django.utils.timezone.now')
    def test_add_event_multiroom_enabled(self, now_patch):
        self._test_add_event_common(now_patch, True)

    @patch('django.utils.timezone.now')
    def test_add_event_in_past(self, now_patch):
        now_patch.return_value = self._fake_now

        event_count_before = Event.objects.count()

        url = reverse("add-event")
        response = self.client.post(url, data={
            "start": "30/05/2013 20:00",
            "duration": "01:30:00",
            "number_of_days": "3",
            "event_name": "Ev\u0119nt of choic\u0119",
            "event_template": "1",
            "booked_by": "\u015Comeb\u014ddy",
            "private": "on",
            "outside_hire": "",
            "confirmed": "on",
            "discounted": "on",
        })
        # Request succeeded?
        self.assertEqual(response.status_code, 200)

        # Event shouldn't have been added:
        self.assertEqual(event_count_before, Event.objects.count())

        self.assertTemplateUsed(response, "form_new_event_and_showing.html")

        # Check error was as expected:
        self.assertFormError(response, 'form', 'start',
                             'Must be in the future')

    @patch('django.utils.timezone.now')
    def test_add_event_missing_fields(self, now_patch):
        now_patch.return_value = self._fake_now

        event_count_before = Event.objects.count()

        url = reverse("add-event")
        response = self.client.post(url, data={
            "start": "",
            "duration": "",
            "number_of_days": "",
            "event_name": "",
            "event_template": "",
            "booked_by": "",
            "private": "",
            "outside_hire": "",
            "confirmed": "",
            "discounted": "",
        })
        # Request succeeded?
        self.assertEqual(response.status_code, 200)

        # Event shouldn't have been added:
        self.assertEqual(event_count_before, Event.objects.count())

        self.assertTemplateUsed(response, "form_new_event_and_showing.html")

        # Check errors as expected:
        self.assertFormError(response, 'form', 'start',
                             'This field is required.')
        self.assertFormError(response, 'form', 'duration',
                             'This field is required.')
        self.assertFormError(
            response, 'form', 'number_of_days', 'This field is required.')
        self.assertFormError(response, 'form', 'event_name',
                             'This field is required.')
        self.assertFormError(response, 'form', 'booked_by',
                             'This field is required.')
        self.assertFormError(
            response, 'form', 'event_template', 'This field is required.')


class EditEventView(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(EditEventView, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def test_get_edit_event_form_no_media_no_legacy_copy(self):
        url = reverse("edit-event-details", kwargs={"event_id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_event.html")

        self.assertContains(response, "Event one title")
        self.assertContains(response, "Event one copy")
        self.assertContains(response, "Event one copy summary")
        self.assertContains(response, "PRICING_ONE")
        self.assertContains(response, "PRETITLE One")
        self.assertContains(response, "POSTTITLE One")
        self.assertContains(response, "FILM_INFO_One")
        self.assertContains(response, "01:30:00")
        self.assertContains(response,
                            '<input id="id_outside_hire" checked="checked" '
                            'name="outside_hire" type="checkbox" />',
                            html=True)
        self.assertContains(response,
                            '<input id="id_private" name="private" '
                            'type="checkbox" />',
                            html=True)
        # Blah. It's probably fine. Ahem.

    def test_get_edit_event_form_no_media_legacy_copy(self):
        # Test the transformation of legacy copy properly in a separate set of
        # tests...

        url = reverse("edit-event-details", kwargs={"event_id": 2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_event.html")

        self.assertContains(response, "Event two title")
        # newlines -> <br>
        self.assertContains(response, "Event <br>\n two <br>\n copy")
        self.assertContains(response,
                            "Event two\n copy summary")  # not stripped
        self.assertContains(response, "01:30:00")
        self.assertContains(response,
                            '<input id="id_outside_hire" name="outside_hire" '
                            'type="checkbox" />',
                            html=True)
        self.assertContains(response,
                            '<input id="id_private" name="private" '
                            'type="checkbox" />',
                            html=True)
        # It's probably still fine. Cough.

    @override_settings(MEDIA_ROOT="/tmp")
    def test_get_edit_event_form_media_item(self):
        with tempfile.NamedTemporaryFile(dir="/tmp",
                                         prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            # Add MediaItem to event 1:
            media_item = MediaItem(
                media_file=temp_jpg.name, mimetype="image/jpeg",
                caption="Image Caption!", credit="Image Credit!")
            media_item.save()
            event = Event.objects.get(id=1)
            event.media.add(media_item)
            event.save()

            # Get page:
            url = reverse("edit-event-details", kwargs={"event_id": 1})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "form_event.html")

            self.assertContains(response, media_item.media_file)
            # Submit the minimum amount of data to validate:
            self.assertContains(response, "Image Credit!")
            # Caption not currently exposed to user

    def test_get_edit_missing_event(self):
        url = reverse("edit-event-details", kwargs={"event_id": 1000})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_edit_missing_event(self):
        url = reverse("edit-event-details", kwargs={"event_id": 1000})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_post_edit_event_no_media_missing_data(self):
        url = reverse("edit-event-details", kwargs={"event_id": 1})
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_event.html")

        self.assertFormError(response, 'form', 'name',
                             'This field is required.')
        self.assertFormError(response, 'form', 'duration',
                             'This field is required.')

    def test_post_edit_event_no_media_minimal_data(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        # Submit the minimum amount of data to validate:
        response = self.client.post(url, data={
            'name': 'New \u20acvent Name',
            'duration': '00:10:00',
        })
        self.assert_return_to_index(response)

        event = Event.objects.get(id=2)
        self.assertEqual(event.name, 'New \u20acvent Name')
        self.assertEqual(event.pre_title, '')
        self.assertEqual(event.post_title, '')
        self.assertEqual(event.pricing, '')
        self.assertEqual(event.film_information, '')
        self.assertEqual(event.duration, time(0, 10))
        self.assertEqual(event.copy, '')
        self.assertEqual(event.copy_summary, '')
        self.assertEqual(event.terms, '')
        self.assertEqual(event.notes, '')
        self.assertEqual(event.media.count(), 0)
        self.assertEqual(event.outside_hire, False)
        self.assertEqual(event.private, False)
        # Shouldn't have changed:
        self.assertEqual(event.legacy_id, '100')

    def test_post_edit_event_no_media_all_fields(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        # Submit the minimum amount of data to validate:
        response = self.client.post(url, data={
            'name': 'New \u20acvent Name!',
            'duration': '01:10:09',
            'copy': 'Some more copy',
            'copy_summary': 'Copy summary blah',
            'pre_title': 'The thing that will be',
            'post_title': 'The thing that was',
            'pricing': 'Full \u00A35',
            'film_information': 'Blah blah films',
            'terms': 'Always term time',
            'notes': 'This is getting\n boring',
            'outside_hire': 'on',
            'private': 'on',
        })
        self.assert_return_to_index(response)

        event = Event.objects.get(id=2)
        self.assertEqual(event.name, 'New \u20acvent Name!')
        self.assertEqual(event.duration, time(1, 10, 9))
        self.assertEqual(event.copy, 'Some more copy')
        self.assertEqual(event.copy_summary, 'Copy summary blah')
        self.assertEqual(event.terms, 'Always term time')
        self.assertEqual(event.notes, 'This is getting\n boring')
        self.assertEqual(event.media.count(), 0)
        self.assertEqual(event.outside_hire, True)
        self.assertEqual(event.private, True)
        self.assertEqual(event.legacy_id, '100')
        self.assertEqual(event.pre_title, 'The thing that will be')
        self.assertEqual(event.post_title, 'The thing that was')
        self.assertEqual(event.pricing, 'Full \u00a35')
        self.assertEqual(event.film_information, 'Blah blah films')
        # Shouldn't have changed:
        self.assertEqual(event.legacy_id, '100')

    @patch("toolkit.util.image.get_mimetype")
    def test_post_edit_event_add_media_invalid_empty(self, get_mimetype_patch):

        url = reverse("edit-event-details", kwargs={"event_id": 2})

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_jpg,
            })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_event.html")
        self.assertFormError(response, 'media_form',
                             'media_file', 'The submitted file is empty.')

        self.assertFalse(get_mimetype_patch.called)

        event = Event.objects.get(id=2)
        self.assertEqual(event.media.count(), 0)

    def test_post_edit_event_add_media_not_an_image(self):

        url = reverse("edit-event-details", kwargs={"event_id": 2})

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            temp_jpg.write(b"Not an empty jpeg")
            temp_jpg.seek(0)
            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_jpg,
                'credit': 'All new image credit!'
            })

        self.assertFormError(
            response, 'media_form', 'media_file',
            'Upload a valid image. The file you uploaded was either '
            'not an image or a corrupted image.')

        event = Event.objects.get(id=2)
        self.assertEqual(event.media.count(), 0)

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_edit_event_add_media_jpeg(self):

        url = reverse("edit-event-details", kwargs={"event_id": 2})

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            # used for assertion:
            temp_file_name = os.path.basename(temp_jpg.name)
            temp_jpg.write(TINY_VALID_JPEG)
            temp_jpg.seek(0)
            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_jpg,
                'credit': 'All new image credit!'
            })

        self.assert_return_to_index(response)

        event = Event.objects.get(id=2)
        self.assertEqual(event.media.count(), 1)
        media_item = event.media.all()[0]
        self.assertEqual(media_item.mimetype, "image/jpeg")
        self.assertEqual(media_item.credit, 'All new image credit!')
        self.assertEqual(media_item.caption, None)
        self.assertEqual(media_item.media_file.name,
                         os.path.join("diary", temp_file_name))

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_edit_event_add_media_png(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".png") as temp_png:
            # used for assertion:
            temp_file_name = os.path.basename(temp_png.name)

            temp_png.write(TINY_VALID_PNG)
            temp_png.seek(0)
            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_png,
                'credit': 'All new image credit!'
            })

        self.assert_return_to_index(response)

        event = Event.objects.get(id=2)
        self.assertEqual(event.media.count(), 1)
        media_item = event.media.all()[0]
        self.assertEqual(media_item.mimetype, "image/png")
        self.assertEqual(media_item.credit, 'All new image credit!')
        self.assertEqual(media_item.caption, None)
        self.assertEqual(media_item.media_file.name,
                         os.path.join("diary", temp_file_name))

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_edit_event_clear_media(self):
        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            # Add MediaItem to event 1:
            media_item = MediaItem(
                media_file=temp_jpg.name, mimetype="image/jpeg",
                caption="Image Caption!", credit="Image Credit!")
            media_item.save()
            event = Event.objects.get(id=2)
            event.media.add(media_item)
            event.save()

            url = reverse("edit-event-details", kwargs={"event_id": 2})

            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_jpg.name,
                'media_file-clear': 'on',
            })
            self.assert_return_to_index(response)

            event = Event.objects.get(id=2)
            # Media item should be gone:
            self.assertEqual(event.media.count(), 0)

    @override_settings(MEDIA_ROOT="/tmp", PROGRAMME_MEDIA_MAX_SIZE_MB=1)
    def test_post_edit_event_add_media_too_big(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            # Write 1 MB + 1 byte, consisting of valid JPEG data followed by
            # nulls:
            temp_jpg.write(TINY_VALID_JPEG)
            temp_jpg.write(b'\0' * (1024 - len(TINY_VALID_JPEG)))

            one_k_data = b"\0" * 1024
            for _ in six.moves.range(1023):
                temp_jpg.write(one_k_data)
            # the extra byte!
            temp_jpg.write(b'\0')
            temp_jpg.seek(0)

            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_jpg,
                'credit': 'All new image credit!'
            })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_event.html")
        self.assertFormError(
            response, 'media_form', 'media_file',
            'Media file must be 1 MB or less (uploaded file is 1.00 MB)')

        event = Event.objects.get(id=2)
        self.assertEqual(event.media.count(), 0)

    @override_settings(MEDIA_ROOT="/tmp", PROGRAMME_MEDIA_MAX_SIZE_MB=1)
    def test_post_edit_event_add_media_max_size(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-",
                                         suffix=".jpg") as temp_jpg:
            # Write 1 MB, consisting of valid JPEG data followed by
            # nulls:
            temp_jpg.write(TINY_VALID_JPEG)
            temp_jpg.write(b'\0' * (1024 - len(TINY_VALID_JPEG)))

            one_k_data = b"\0" * 1024
            for _ in six.moves.range(1023):
                temp_jpg.write(one_k_data)
            temp_jpg.seek(0)

            response = self.client.post(url, data={
                'name': 'New \u20acvent Name',
                'duration': '00:10:00',
                'media_file': temp_jpg,
                'credit': 'All new image credit!'
            })
        self.assert_return_to_index(response)

    @override_settings(PROGRAMME_COPY_SUMMARY_MAX_CHARS=50)
    def test_post_edit_event_too_much_copy_summary(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        original_summary = Event.objects.get(id=2).copy_summary
        copy_summary_data = "X" * 51

        # Submit the minimum amount of data to validate, plus some overly-long
        # copy summary data:
        response = self.client.post(url, data={
            'name': 'New \u20acvent Name',
            'duration': '00:10:00',
            'copy_summary': copy_summary_data,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_event.html")
        self.assertFormError(
            response, 'form', 'copy_summary',
            'Copy summary must be 50 characters or fewer '
            '(currently 51 characters)')

        event = Event.objects.get(id=2)
        self.assertEqual(event.copy_summary, original_summary)

    @override_settings(PROGRAMME_COPY_SUMMARY_MAX_CHARS=50)
    def test_post_edit_event_just_enough_copy_summary(self):
        url = reverse("edit-event-details", kwargs={"event_id": 2})

        copy_summary_data = "X" * 50

        # Submit the minimum amount of data to validate, plus some overly-long
        # copy summary data:
        response = self.client.post(url, data={
            'name': 'New \u20acvent Name',
            'duration': '00:10:00',
            'copy_summary': copy_summary_data,
        })

        self.assert_return_to_index(response)

        event = Event.objects.get(id=2)
        self.assertEqual(event.copy_summary, copy_summary_data)


class EditIdeasViewTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(EditIdeasViewTests, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def test_get_form_no_existing_ideas(self):
        # Confirm no ideas in the database for Jan 2012:
        self.assertQuerysetEqual(
            DiaryIdea.objects.all().filter(month=date(2012, 1, 1)), [])

        # Get the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_idea.html")

        # There should now be a Jan 2012 entry in the DB:
        idea = DiaryIdea.objects.get(month=date(2012, 1, 1))
        # With no content:
        self.assertIsNone(idea.ideas)

    def test_get_json_no_existing_ideas(self):
        # Confirm no ideas in the database for Jan 2012:
        self.assertQuerysetEqual(
            DiaryIdea.objects.all().filter(month=date(2012, 1, 1)), [])

        # Get the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.get(
            url, HTTP_ACCEPT="Accept: application/xml;q=0.9, "
            "*/*;q=0.8, application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data, {
            "ideas": None,
            'month': '2012-01-01',
        })
        self.assertTemplateNotUsed(response, "form_idea.html")

        # There should now be a Jan 2012 entry in the DB:
        idea = DiaryIdea.objects.get(month=date(2012, 1, 1))
        # With no content:
        self.assertIsNone(idea.ideas)

    def test_get_form_existing_ideas(self):
        # Ensure there's something in the DB for Jan 2012:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertTrue(created)  # Not strictly necessary
        idea.ideas = "An ide\u0113 f\u014d\u0159 some \u20acvent"
        idea.save()

        # Get the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_idea.html")

        self.assertContains(
            response, "An ide\u0113 f\u014d\u0159 some \u20acvent")

    def test_get_json_existing_idea(self):
        # Ensure there's something in the DB for Jan 2012:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertTrue(created)  # Not strictly necessary
        idea.ideas = "An ide\u0113 f\u014d\u0159 some \u20acvent"
        idea.save()

        # Get the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.get(
            url,
            HTTP_ACCEPT="Accept: application/xml;q=0.9, */*;q=0.8, "
            "application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response["Content-Type"],
                         "application/json; charset=utf-8")
        self.assertEqual(response_data, {
            "ideas": "An ide\u0113 f\u014d\u0159 some \u20acvent",
            'month': '2012-01-01',
        })
        self.assertTemplateNotUsed(response, "form_idea.html")

    def test_post_form_no_existing_idea(self):
        # Confirm no ideas in the database for Jan 2012:
        self.assertQuerysetEqual(
            DiaryIdea.objects.all().filter(month=date(2012, 1, 1)), [])

        # Post an idea to the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.post(url, data={
            "ideas": "An ide\u0113 f\u014d\u0159 some \u20acvent",
        })

        # Check that's made it into the database:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertFalse(created)
        self.assertEqual(
            idea.ideas, "An ide\u0113 f\u014d\u0159 some \u20acvent")

        self.assert_return_to_index(response)

    def test_post_form_existing_idea(self):
        # Ensure there's something in the DB for Jan 2012:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertTrue(created)  # Not strictly necessary
        idea.ideas = "Any old junk, which shall be overwritten"
        idea.save()

        # Post an idea to the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.post(url, data={
            "ideas": "An ide\u0113 f\u014d\u0159 some \u20acvent",
        })

        # Check that's made it into the database:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertFalse(created)
        self.assertEqual(
            idea.ideas, "An ide\u0113 f\u014d\u0159 some \u20acvent")

        self.assert_return_to_index(response)

    def test_post_inline_existing_idea(self):
        # Ensure there's something in the DB for Jan 2012:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertTrue(created)  # Not strictly necessary
        idea.ideas = "Any old junk, which shall be overwritten"
        idea.save()

        new_idea = "An ide\u0113 f\u014d\u0159 some \u20acvent"

        # Post an idea to the corresponding edit form:
        url = reverse("edit-ideas", kwargs={"year": 2012, "month": 1})
        response = self.client.post(url, data={
            "ideas": new_idea,
            "source": "inline",
        })

        # Check that's made it into the database:
        idea, created = DiaryIdea.objects.get_or_create(month=date(2012, 1, 1))
        self.assertFalse(created)
        self.assertEqual(idea.ideas, new_idea)

        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertEqual(response.content, new_idea.encode("utf8"))


class ViewEventFieldTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(ViewEventFieldTests, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

        # Fake "now()" function to return a fixed time:
        self.time_patch = patch('django.utils.timezone.now')
        self.time_mock = self.time_patch.start()
        self.time_mock.return_value = self._fake_now

    def tearDown(self):
        self.time_patch.stop()

    def test_view_event_field_rota(self):
        url = reverse("view_event_field", kwargs={"field": "rota"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_rota.html")

        self.assertNotContains(response, "Event three title")
        self.assertContains(response, "Event four titl\u0113")
        self.assertContains(response, "Role 2 (nonstandard)-1")

    def test_view_event_field_copy(self):
        url = reverse("view_event_field", kwargs={"field": "copy"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_copy.html")

        self.assertNotContains(response, "EVENT THREE TITLE")
        self.assertContains(
            response, "Sun 09 18:00 .... Event four titl\u0113")
        self.assertContains(
            response, "<p>EVENT FOUR TITL\u0112</p>", html=True)
        self.assertContains(
            response, "<p>Event four C\u014dpy</p>", html=True)

    def test_view_event_field_copy_summary(self):
        url = reverse("view_event_field", kwargs={"field": "copy_summary"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_copy_summary.html")

        self.assertNotContains(response, "EVENT THREE TITLE")
        self.assertContains(response,
                            'Sun 09 18:00 .... Pretitle four Event four '
                            'titl\u0113 Posttitle four')
        self.assertContains(response,
                            '<p class="title">Event four titl\u0113</p>',
                            html=True)
        self.assertContains(response,
                            '<p class="copy_summary">\u010copy four '
                            'summary</p>',
                            html=True)

        self.assertContains(response, "\u00a3milliion per thing")
        self.assertContains(response, "Pretitle four")
        self.assertContains(response, "Posttitle four")
        self.assertContains(response, "Film info for four")

    def test_view_event_field_terms(self):
        url = reverse("view_event_field", kwargs={"field": "terms"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_terms.html")

        self.assertContains(
            response, "Sun 09 18:00 .... Event four titl\u0113")
        self.assertContains(response, "Cube event / Public event / Confirmed")
        self.assertContains(response, "Terminal price: \u00a31 / \u20ac3")

    def test_custom_start_date_rota_long_time(self):
        # Reverse doesn't work for full date, as regex is apparently too
        # complicated:
        url = reverse("view_event_field", kwargs={"field": "rota"})
        url += "/2013/01/01?daysahead=365"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_rota.html")

        self.assertContains(response, "Event three title")
        self.assertContains(response, "Event four titl\u0113")

    def test_custom_start_date_rota_less_long_time(self):
        # Now shorter date range, should find one fewer event
        url = reverse("view_event_field", kwargs={"field": "rota"})
        url += "/2013/01/01?daysahead=120"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_rota.html")

        self.assertContains(response, "Event three title")
        self.assertNotContains(response, "Event four titl\u0113")

    def test_custom_start_date_rota_invalid_date(self):
        # Now shorter date range, should find one fewer event
        url = reverse("view_event_field", kwargs={"field": "rota"})
        url += "/2013/99/99?daysahead=120"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_custom_start_date_terms_search_success(self):
        url = reverse("view_event_field", kwargs={"field": "terms"})
        url += "/2013/01/01?daysahead=365&search=Terminal"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_terms.html")

        self.assertNotContains(response, "EVENT THREE TITLE")
        self.assertContains(response, "EVENT FOUR TITL\u0112")

    def test_custom_start_date_terms_search_no_result(self):
        url = reverse("view_event_field", kwargs={"field": "terms"})
        url += "/2013/01/01?daysahead=365&search=elephant"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_terms.html")

        self.assertNotContains(response, "EVENT THREE TITLE")
        self.assertNotContains(response, "EVENT FOUR TITL\u0112")


class PreferencesTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(PreferencesTests, self).setUp()
        # Log in:
        self.client.login(username="admin", password="T3stPassword!")

    def _get_edit_prefs(self, response):
        match = re.search(
            r"var\s+edit_prefs\s*=\s*({.*?});",
            response.content.decode("utf-8"), re.DOTALL)
        return json.loads(match.group(1))

    def test_set_pref(self):
        url = reverse("default-edit")

        # Get current prefs:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "true")

        # Set popups false:
        response = self.client.get(reverse("set_edit_preferences"),
                                   data={"popups": "false"})
        self.assertEqual(response.status_code, 200)

        # Verify change:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "false")

        # Back to true:
        response = self.client.get(reverse("set_edit_preferences"),
                                   data={"popups": "true"})
        self.assertEqual(response.status_code, 200)

        # Verify change:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "true")

    def test_set_get_single_pref(self):
        session_mock = {}
        toolkit.diary.edit_prefs.set_preference(session_mock, 'daysahead', 30)

        retrieved_pref = toolkit.diary.edit_prefs.get_preference(
            session_mock, 'daysahead')
        self.assertEqual(retrieved_pref, '30')

    def test_set_get_single_missing_pref(self):
        session_mock = {}
        retrieved_pref = toolkit.diary.edit_prefs.get_preference(
            session_mock, 'daysahead')
        self.assertEqual(retrieved_pref, '365')

    def test_set_get_single_bad_pref(self):
        session_mock = {'spangles': 'foo'}
        # Shouldn't return the value, as it's not a known pref, even tho it's
        # in the session:
        retrieved_pref = toolkit.diary.edit_prefs.get_preference(
            session_mock, 'spangles')
        self.assertEqual(retrieved_pref, None)

    def test_bad_value(self):
        url = reverse("default-edit")

        # Set popups something stupid:
        response = self.client.get(reverse("set_edit_preferences"),
                                   data={"popups": "tralala" * 100})
        self.assertEqual(response.status_code, 200)

        # Verify change:
        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(edit_prefs["popups"], "tralalatra")

    def test_bad_pref(self):
        url = reverse("default-edit")

        # Set weird value, verify it doesn't come out in the edit page:
        response = self.client.get(reverse("set_edit_preferences"),
                                   data={"nonsense": "tralala"})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        edit_prefs = self._get_edit_prefs(response)
        self.assertEqual(set(edit_prefs.keys()), {"daysahead", "popups"})

    def test_redirect_change(self):
        url = reverse("cancel-edit")
        # default to javscript hackery:
        response = self.client.get(url)
        self.assert_return_to_index(response)

        # Set popup preference false:
        response = self.client.get(reverse("set_edit_preferences"),
                                   data={"popups": "false"})
        self.assertEqual(response.status_code, 200)

        # should now 302 to edit list:
        response = self.client.get(url)
        self.assertRedirects(response, reverse("default-edit"))


class EditTagsViewTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(EditTagsViewTests, self).setUp()
        self.client.login(username="admin", password="T3stPassword!")

    def tearDown(self):
        self.client.logout()

    def test_page_loads(self):
        url = reverse("edit_event_tags")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_event_tags.html")

    def test_post_noop(self):
        initial_tag_count = EventTag.objects.count()

        url = reverse("edit_event_tags")
        response = self.client.post(url, data={
            "deleted_tags[]": [],
            "new_tags[]": [],
        })
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data['failed'], False)

        final_tag_count = EventTag.objects.count()
        self.assertEqual(initial_tag_count, final_tag_count)

    def test_post_delete(self):
        url = reverse("edit_event_tags")
        response = self.client.post(url, data={
            "deleted_tags[]": [1, 3],
            "new_tags[]": [],
        })
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data['failed'], False)

        self.assertEqual(EventTag.objects.filter(id=1).count(), 0)
        self.assertEqual(EventTag.objects.filter(id=2).count(), 1)
        self.assertEqual(EventTag.objects.filter(id=3).count(), 0)

    def test_post_add(self):
        url = reverse("edit_event_tags")
        response = self.client.post(url, data={
            "deleted_tags[]": [],
            "new_tags[]": ["new_tag_one", "new_tag_TWO "],
        })
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data['failed'], False)

        nt1 = EventTag.objects.get(name="new_tag_one")
        nt2 = EventTag.objects.get(name="new_tag_two")

        self.assertEqual(nt1.read_only, False)
        self.assertEqual(nt2.read_only, False)

    def test_post_bad_delete(self):
        initial_tag_count = EventTag.objects.count()

        url = reverse("edit_event_tags")
        response = self.client.post(url, data={
            "deleted_tags[]": [1000],
            "new_tags[]": [],
        })
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data['failed'], True)
        self.assertIn('delete', response_data['errors'])

        final_tag_count = EventTag.objects.count()
        self.assertEqual(initial_tag_count, final_tag_count)

    def test_post_duplicate_new_tag(self):
        initial_tag_count = EventTag.objects.count()

        existing_name = EventTag.objects.get(id=1).name

        url = reverse("edit_event_tags")
        response = self.client.post(url, data={
            "deleted_tags[]": [1],
            "new_tags[]": [existing_name],
        })
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(response_data['failed'], True)
        self.assertEqual(
            response_data['errors'],
            {existing_name: ['Event tag with this Name already exists.']}
        )
        final_tag_count = EventTag.objects.count()
        self.assertEqual(initial_tag_count, final_tag_count)


class DiaryCalendarViewTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(DiaryCalendarViewTests, self).setUp()
        self.client.login(username="admin", password="T3stPassword!")

    def _get_room_list(self, response):
        match = re.search(
            r"init_calendar_view\((?:.*?,){5}\s*(?P<room_list>\[.*?\])\);",
            response.content.decode("utf-8"), re.DOTALL)
        return match.group("room_list")

    @override_settings(MULTIROOM_ENABLED=False)
    def test_view_default(self):
        url = reverse("diary-edit-calendar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_event_calendar_index.html')

        self.assertJSONEqual(self._get_room_list(response), [])

    @override_settings(MULTIROOM_ENABLED=True)
    def test_view_default_multiroom_enabled(self):
        url = reverse("diary-edit-calendar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_event_calendar_index.html')

        self.assertJSONEqual(self._get_room_list(response), [
            {u'id': 1, u'title': u'Room one'},
            {u'id': 2, u'title': u'Room two'}])

    def test_view_year_month_day(self):
        url = reverse("diary-edit-calendar") + "/2013/1/30/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_event_calendar_index.html')

    def test_view_year_month(self):
        url = reverse("diary-edit-calendar") + "/2013/1/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_event_calendar_index.html')

    def test_view_year_bad_url(self):
        url = reverse("diary-edit-calendar") + "/2013/0/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        url = reverse("diary-edit-calendar") + "/2013/13/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        url = reverse("diary-edit-calendar") + "/fruitbat"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view_year(self):
        url = reverse("diary-edit-calendar") + "/2013/"
        response = self.client.get(url)
        # Shouldn't work!
        self.assertEqual(response.status_code, 404)


class DiaryDataViewTests(DiaryTestsMixin, TestCase):

    def setUp(self):
        super(DiaryDataViewTests, self).setUp()
        self.client.login(username="admin", password="T3stPassword!")

    def test_missing_params(self):
        url = reverse("edit-diary-data")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_invalid_end(self):
        # Valid start, invalid end
        url = reverse("edit-diary-data")
        response = self.client.get(url, data={
            "start": "2000-01-01",
            "end": "0"
        })
        self.assertEqual(response.status_code, 404)

    # Common code for following two tests
    def _common_test_valid_query(self, now_patch, multiroom_enabled):
        now_patch.return_value = self._fake_now

        # Always set a room, even if multiroom disabled - the retrieved data
        # shouldn't show this if multiroom is disabled:
        showing = Showing.objects.get(id=2)
        showing.room_id = self.room_2.id
        showing.save(force=True)

        CONFIRMED_IN_PAST = "#FF9080"
        CONFIRMED_IN_FUTURE = "#C70040"
        UNCONFIRMED = "#E0CFCF"

        url = reverse("edit-diary-data")
        with self.settings(
                CALENDAR_CONFIRMED_IN_PAST_COLOUR=CONFIRMED_IN_PAST,
                CALENDAR_CONFIRMED_IN_FUTURE_COLOUR=CONFIRMED_IN_FUTURE,
                CALENDAR_UNCONFIRMED_COLOUR=UNCONFIRMED):
            response = self.client.get(url, data={
                "start": "2013-02-15",
                "end": "2013-09-13",
            })

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content.decode("utf-8"))
        data_by_showing = {int(i['id']): i for i in data}

        expected_showings = {1, 2, 3, 4, 5, 6, 7, 10}

        self.assertEqual(set(data_by_showing.keys()), expected_showings)

        expected_data = {
            1: {
                "id": 1,
                "className": [],
                "color": UNCONFIRMED,
                "end": "2013-04-01T20:30:00+01:00",
                "start": "2013-04-01T19:00:00+01:00",
                "title": "Event two title",
                "url": "/diary/edit/event/id/2/view/"
            },
            2: {
                "id": 2,
                "className": [],
                "color": CONFIRMED_IN_PAST,
                "end": "2013-04-02T20:30:00+01:00",
                "start": "2013-04-02T19:00:00+01:00",
                "title": "Event two title",
                "url": "/diary/edit/event/id/2/view/"
            },
            3: {
                "id": 3,
                "className": [
                    "s_cancelled"
                ],
                "color": CONFIRMED_IN_PAST,
                "end": "2013-04-03T20:30:00+01:00",
                "start": "2013-04-03T19:00:00+01:00",
                "title": "Event two title",
                "url": "/diary/edit/event/id/2/view/"
            },
            4: {
                "id": 4,
                "className": ['s_private'],
                "color": CONFIRMED_IN_PAST,
                "end": "2013-04-04T20:30:00+01:00",
                "start": "2013-04-04T19:00:00+01:00",
                "title": "Event two title",
                "url": "/diary/edit/event/id/2/view/"
            },
            5: {
                "id": 5,
                "className": ["s_cancelled", "s_private"],
                "color": CONFIRMED_IN_PAST,
                "end": "2013-04-05T20:30:00+01:00",
                "start": "2013-04-05T19:00:00+01:00",
                "title": "Event two title",
                "url": "/diary/edit/event/id/2/view/"
            },
            6: {
                "id": 6,
                "className": [],
                "color": CONFIRMED_IN_PAST,
                "end": "2013-04-13T21:00:00+01:00",
                "start": "2013-04-13T18:00:00+01:00",
                "title": "Event three title",
                "url": "/diary/edit/event/id/3/view/"
            },
            7: {
                "id": 7,
                "className": [],
                "color": CONFIRMED_IN_FUTURE,
                "end": "2013-06-09T19:00:00+01:00",
                "start": "2013-06-09T18:00:00+01:00",
                "title": "Event four titl\u0113",
                "url": "/diary/edit/showing/id/7/"
            },
            10: {
                "id": 10,
                "className": ["s_private", "s_outside_hire"],
                "color": CONFIRMED_IN_PAST,
                "end": "2013-02-15T19:30:00+00:00",
                "start": "2013-02-15T18:00:00+00:00",
                "title": "Event one title",
                "url": "/diary/edit/event/id/1/view/"
            },
        }

        if multiroom_enabled:
            for showing_id in expected_data:
                # Showing 2 room is set above
                expected_data[showing_id]['resourceId'] = (
                        2 if showing_id == 2 else None)


        for sid in expected_showings:
            s_data = data_by_showing[sid]
            self.assertEqual(expected_data[sid], s_data)

    @override_settings(MULTIROOM_ENABLED=False)
    @patch('django.utils.timezone.now')
    def test_valid_query(self, now_patch):
        self._common_test_valid_query(now_patch, False)

    @override_settings(MULTIROOM_ENABLED=True)
    @patch('django.utils.timezone.now')
    def test_valid_query_multiroom_enabled(self, now_patch):
        self._common_test_valid_query(now_patch, True)
