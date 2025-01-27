from __future__ import absolute_import
from re import I

import zoneinfo
from datetime import datetime, date, timedelta

from django.test import TestCase

import django.db
from django.core.exceptions import ValidationError
from toolkit.diary.models import (
    Showing,
    Event,
    PrintedProgramme,
    EventTag,
    Role,
)

from .common import DiaryTestsMixin, NowPatchMixin

UTC = zoneinfo.ZoneInfo("UTC")


class ShowingModelSave(DiaryTestsMixin, NowPatchMixin, TestCase):
    def test_can_save_future_showing(self):
        self.e4s3.save()

    def test_can_amend_future_showing(self):
        self.e4s3.start = self._fake_now + timedelta(days=1)
        self.e4s3.save()

    def test_cannot_save_historic_showing(self):
        with self.assertRaisesMessage(
            django.db.utils.IntegrityError,
            "Can't update showings that start in the past",
        ):
            self.e2s1.save()

    def test_cannot_move_date_of_historic_showing(self):
        self.e2s1.start = self._fake_now + timedelta(days=1)
        with self.assertRaisesMessage(
            django.db.utils.IntegrityError,
            "Can't update showings that start in the past",
        ):
            self.e2s1.save()

    def test_cannot_move_showing_into_past(self):
        self.e4s3.start = self._fake_now - timedelta(days=1)
        with self.assertRaisesMessage(
            django.db.utils.IntegrityError,
            "Can't update showings that start in the past",
        ):
            self.e4s3.save()


class ShowingModelDelete(DiaryTestsMixin, NowPatchMixin, TestCase):
    def test_can_delete_future_showing(self):
        self.e4s3.delete()

    def test_cannot_delete_historic_showing(self):
        with self.assertRaisesMessage(
            django.db.utils.IntegrityError,
            "Can't delete showings that start in the past",
        ):
            self.e2s1.delete()

    def test_cannot_move_date_of_historic_showing_to_delete(self):
        self.e2s1.start = self._fake_now + timedelta(days=1)
        with self.assertRaisesMessage(
            django.db.utils.IntegrityError,
            "Can't delete showings that start in the past",
        ):
            self.e2s1.delete()

    def test_delete_unsaved_instance(self):
        s = Showing()
        with self.assertRaises(ValueError):
            s.delete()


class ShowingModelMethods(DiaryTestsMixin, NowPatchMixin, TestCase):
    def test_in_past_when_future(self):
        self.assertFalse(self.e4s3.in_past())

    def test_in_past_when_past(self):
        self.assertTrue(self.e2s1.in_past())

    def test_in_past_new_instance(self):
        s = Showing()
        self.assertFalse(s.in_past())


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
        self.assertEqual(len(records), 9)
        for showing in records:
            self.assertFalse(showing.cancelled)

    def test_manager_confirmed(self):
        records = list(Showing.objects.confirmed())
        # From the fixtures, there are 7 showings that are confirmed:
        self.assertEqual(len(records), 8)
        for showing in records:
            self.assertTrue(showing.confirmed)

    def test_manager_date_range(self):
        start = datetime(2013, 4, 2, 12, 0, tzinfo=UTC)
        end = datetime(2013, 4, 4, 12, 0, tzinfo=UTC)
        records = list(Showing.objects.start_in_range(start, end))
        # Expect 2 showings in this date range:
        self.assertEqual(len(records), 2)
        for showing in records:
            self.assertTrue(showing.start < end)
            self.assertTrue(showing.start > start)

    def test_queryset_chaining(self):
        start = datetime(2000, 4, 2, 12, 0, tzinfo=UTC)
        end = datetime(2013, 9, 1, 12, 0, tzinfo=UTC)
        records = list(
            Showing.objects.all()
            .public()
            .not_cancelled()
            .start_in_range(start, end)
            .confirmed()
        )
        self.assertEqual(len(records), 3)
        for showing in records:
            self.assertTrue(showing.confirmed)
            self.assertFalse(showing.hide_in_programme)
            self.assertFalse(showing.event.private)
            self.assertFalse(showing.cancelled)
            self.assertTrue(showing.start < end)
            self.assertTrue(showing.start > start)
            self.assertTrue(showing.confirmed)


class EventModelNonLegacyCopy(TestCase):
    def setUp(self):
        self.sample_copy = (
            "<p>Simple &amp; tidy HTML/unicode \u00a9\u014dpy\n</p>\n"
            "<p>With a <a href='http://example.com/foo/'>link!</a>"
            "<p>And another! <a href='https://example.com/bar/'>link!</a>"
            " and some equivalent things; &pound; &#163; \u00a3<br></p>"
        )
        self.event = Event(
            name="Test event", legacy_copy=False, copy=self.sample_copy
        )
        self.event.save()

    def test_simple(self):
        # Test copy goes in and out without being mangled
        reloaded = Event.objects.get(id=self.event.pk)
        self.assertEqual(reloaded.copy, self.sample_copy)

    def test_html_copy(self):
        self.assertEqual(self.event.copy_html, self.sample_copy)

    def test_plaintext_copy(self):
        expected = (
            "Simple & tidy HTML/unicode \u00a9\u014dpy \n\n"
            "With a link!: http://example.com/foo/\n\n"
            "And another! link!: https://example.com/bar/"
            " and some equivalent things; \u00a3 \u00a3 \u00a3  \n\n"
        )
        self.assertEqual(self.event.copy_plaintext, expected)


class EventModelLegacyCopy(TestCase):
    def setUp(self):
        self.sample_copy = (
            "Simple &amp; tidy legacy \u00a9\u014dpy\n\n"
            "With an unardorned link: http://example.com/foo/"
            " https://example.com/foo/"
            " and some equivalent things; &pound; &#163; \u00a3..."
            " and <this> \"'<troublemaker>'\""
        )
        self.event = Event(
            name="Test event", legacy_copy=True, copy=self.sample_copy
        )
        self.event.save()

    def test_simple(self):
        # Test copy goes in and out without being mangled
        reloaded = Event.objects.get(id=self.event.pk)
        self.assertEqual(reloaded.copy, self.sample_copy)

    def test_html_copy(self):
        expected = (
            "Simple &amp; tidy legacy \u00a9\u014dpy <br><br>"
            "With an unardorned link: "
            '<a href="http://example.com/foo/">http://example.com/foo/</a>'
            ' <a href="https://example.com/foo/">https://example.com/foo/</a>'
            " and some equivalent things; &pound; &#163; \u00a3..."
            " and <this> \"'<troublemaker>'\""
        )
        self.assertEqual(self.event.copy_html, expected)

    def test_plaintext_copy(self):
        expected = (
            "Simple & tidy legacy \u00a9\u014dpy\n\n"
            "With an unardorned link: http://example.com/foo/"
            " https://example.com/foo/"
            " and some equivalent things; \u00a3 \u00a3 \u00a3..."
            " and <this> \"'<troublemaker>'\""
        )
        self.assertEqual(self.event.copy_plaintext, expected)


class PrintedProgrammeModelTests(TestCase):
    def test_month_ok(self):
        pp = PrintedProgramme(programme="/foo/bar", month=date(2010, 2, 1))
        pp.save()

        pp = PrintedProgramme.objects.get(pk=pp.pk)
        self.assertEqual(pp.month, date(2010, 2, 1))

    def test_month_normalised(self):
        pp = PrintedProgramme(programme="/foo/bar", month=date(2010, 2, 2))
        pp.save()

        pp = PrintedProgramme.objects.get(pk=pp.pk)
        self.assertEqual(pp.month, date(2010, 2, 1))


class EventPricingFromTemplate(DiaryTestsMixin, TestCase):
    def test_set_pricing_from_template(self):
        # No pricing specified when creating the event, and pricing specified
        # in the template:
        new_event = Event(
            name="Event Title",
            template=self.tmpl1,
        )
        self.assertEqual(new_event.pricing, "Entry: \u00a35 / \u20ac10")
        new_event.save()
        self.assertEqual(new_event.pricing, "Entry: \u00a35 / \u20ac10")

    def test_dont_set_pricing_from_template(self):
        # Pricing specified when creating the event, and pricing specified in
        # the template:
        new_event = Event(
            name="Event Title",
            pricing="Actual pricing",
            template=self.tmpl1,
        )
        self.assertEqual(new_event.pricing, "Actual pricing")
        new_event.save()
        self.assertEqual(new_event.pricing, "Actual pricing")

    def test_cant_set_pricing_from_template(self):
        # Pricing specified when creating the event, and no pricing specified
        # in the template:
        new_event = Event(
            name="Event Title",
            pricing="Actual pricing",
            template=self.tmpl3,
        )
        self.assertEqual(new_event.pricing, "Actual pricing")
        new_event.save()
        self.assertEqual(new_event.pricing, "Actual pricing")

    def test_set_from_template_no_pricing(self):
        # No pricing specified when creating the event, and no pricing
        # specified in the template:
        new_event = Event(
            name="Event Title",
            template=self.tmpl3,
        )
        self.assertEqual(new_event.pricing, "")
        new_event.save()
        self.assertEqual(new_event.pricing, "")

    def test_no_template(self):
        # Pricing specified when creating the event, and no pricing specified
        # in the template:
        new_event = Event(
            name="Event Title",
            pricing="Actual pricing",
        )
        self.assertEqual(new_event.pricing, "Actual pricing")
        new_event.save()
        self.assertEqual(new_event.pricing, "Actual pricing")


class EventTagsFromTemplate(DiaryTestsMixin, TestCase):
    def test_set_one_tag_from_template(self):
        new_event = Event(
            name="Event Title",
            template=self.tmpl1,
        )
        new_event.save()
        # Tags shouldn't have been set yet:
        self.assertEqual(new_event.tags.count(), 0)

        new_event.reset_tags_to_default()

        self.assertEqual(new_event.tags.count(), 1)
        self.assertEqual(new_event.tags.all()[0].name, "tag one")
        self.assertEqual(new_event.tags.all()[0].slug, "tag-one")

    def test_set_two_tags_from_template(self):
        new_event = Event(
            name="Event Title",
            template=self.tmpl2,
        )
        new_event.save()
        # Tags shouldn't have been set yet:
        self.assertEqual(new_event.tags.count(), 0)

        new_event.reset_tags_to_default()

        self.assertEqual(new_event.tags.count(), 2)
        self.assertEqual(new_event.tags.all()[0].name, "tag one")
        self.assertEqual(new_event.tags.all()[0].slug, "tag-one")
        self.assertEqual(new_event.tags.all()[1].name, "tag three")
        self.assertEqual(new_event.tags.all()[1].slug, "tag-three")

    def test_set_no_tags_from_template(self):
        new_event = Event(
            name="Event Title",
            template=self.tmpl3,
        )
        new_event.save()
        # Tags shouldn't have been set yet:
        self.assertEqual(new_event.tags.count(), 0)

        new_event.reset_tags_to_default()

        # Still no tags
        self.assertEqual(new_event.tags.count(), 0)

    def test_set_tags_no_template(self):
        # No template set, call reset_tags
        new_event = Event(
            name="Event Title",
        )
        new_event.save()
        self.assertEqual(new_event.tags.count(), 0)

        new_event.reset_tags_to_default()

        self.assertEqual(new_event.tags.count(), 0)


class EventTagTests(TestCase):
    def test_can_delete_not_readonly(self):
        tag = EventTag(name="test", slug="test", read_only=False)
        tag.save()
        pk = tag.pk

        tag.delete()

        self.assertEqual(EventTag.objects.filter(id=pk).count(), 0)

    def test_cant_delete_readonly(self):
        tag = EventTag(name="test", slug="test", read_only=True)
        tag.save()
        pk = tag.pk

        tag.delete()

        self.assertEqual(EventTag.objects.filter(id=pk).count(), 1)
        tag = EventTag.objects.get(id=pk)
        self.assertEqual(tag.name, "test")

    def test_can_edit_not_readonly(self):
        tag = EventTag(name="test", slug="test", read_only=False)
        tag.save()
        pk = tag.pk
        # Try to edit:
        tag.name = "crispin"
        tag.sort_order = 0xBAD
        tag.save()

        tag = EventTag.objects.get(id=pk)
        self.assertEqual(tag.name, "crispin")
        self.assertEqual(tag.sort_order, 0xBAD)

    def test_can_change_to_readonly(self):
        tag = EventTag(name="test", slug="test", read_only=False)
        tag.save()
        pk = tag.pk

        tag = EventTag.objects.get(id=pk)
        self.assertFalse(tag.read_only)

        tag.read_only = True
        tag.save()

        tag = EventTag.objects.get(id=pk)
        self.assertTrue(tag.read_only)

        tag.name = "crispin"
        self.assertFalse(tag.save())

    def test_cant_edit_most_of_readonly(self):
        tag = EventTag(name="test", slug="test", read_only=True)
        tag.save()
        pk = tag.pk
        # Try to edit:
        tag.name = "crispin"
        tag.slug = "bert"
        tag.read_only = False
        self.assertFalse(tag.save())

        tag = EventTag.objects.get(id=pk)
        # Things shouldn't change:
        self.assertEqual(tag.name, "test")
        self.assertEqual(tag.slug, "test")
        self.assertEqual(tag.promoted, False)
        self.assertEqual(tag.read_only, True)

    def test_can_edit_readonly_promotion(self):
        tag = EventTag(
            name="test",
            slug="test",
            read_only=True,
            sort_order=1,
            promoted=False,
        )
        tag.save()
        pk = tag.pk
        # Try to edit:
        tag.name = "crispin"
        tag.promoted = True
        tag.read_only = False
        tag.sort_order = 0xF00BA
        self.assertFalse(tag.save())

        tag = EventTag.objects.get(id=pk)
        # Most things shouldn't change:
        self.assertEqual(tag.name, "test")
        self.assertEqual(tag.slug, "test")
        self.assertEqual(tag.read_only, True)
        # Promoted and sort values should:
        self.assertEqual(tag.promoted, True)
        self.assertEqual(tag.sort_order, 0xF00BA)

    def test_clean_case(self):
        tag = EventTag(name="BIGlettersHERE")
        tag.clean()
        self.assertEqual(tag.name, "biglettershere")
        self.assertEqual(tag.slug, "biglettershere")

    def test_slugify(self):
        tag = EventTag(name="with space", slug="")
        tag.clean()
        self.assertEqual(tag.name, "with space")
        self.assertEqual(tag.slug, "with-space")

        tag = EventTag(name="with&ampersand")
        tag.clean()
        self.assertEqual(tag.name, "with&ampersand")
        self.assertEqual(tag.slug, "withampersand")

        tag = EventTag(name="with?questionmark")
        tag.clean()
        self.assertEqual(tag.name, "with?questionmark")
        self.assertEqual(tag.slug, "withquestionmark")

        tag = EventTag(name="with#hash")
        tag.clean()
        self.assertEqual(tag.name, "with#hash")
        self.assertEqual(tag.slug, "withhash")

    def test_reject_blank(self):
        tag = EventTag(name="")
        self.assertRaises(ValidationError, tag.full_clean)

    def test_must_be_unique(self):
        t1 = EventTag(name="jim", slug="jim")
        t1.save()

        t2 = EventTag(name="jim!", slug="jim")
        self.assertRaises(django.db.IntegrityError, t2.save)


class RoleTests(TestCase):
    def test_can_delete_not_readonly(self):
        role = Role(name="Role One")
        role.save()
        pk = role.pk

        role.delete()

        self.assertEqual(Role.objects.filter(id=pk).count(), 0)

    def test_cant_delete_readonly(self):
        role = Role(name="Role One", read_only=True)
        role.save()
        pk = role.pk

        role.delete()
        self.assertEqual(Role.objects.filter(id=pk).count(), 1)

        role_re = Role.objects.get(id=pk)
        self.assertEqual(role_re.name, "Role One")

    def test_can_edit_not_readonly(self):
        role = Role(name="Role One")
        role.save()
        pk = role.pk

        # Try to edit:
        role.name = "Some other thing"
        role.save()

        role = Role.objects.get(id=pk)
        self.assertEqual(role.name, "Some other thing")

    def test_can_change_to_readonly(self):
        role = Role(name="Role One", read_only=False)
        role.save()
        pk = role.pk

        role = Role.objects.get(id=pk)
        self.assertFalse(role.read_only)

        role.read_only = True
        role.save()

        role = Role.objects.get(id=pk)
        self.assertTrue(role.read_only)

        role.name = "Whatever"
        self.assertFalse(role.save())

    def test_cannot_change_from_readonly(self):
        role = Role(name="Role One", read_only=True, standard=False)
        role.save()
        pk = role.pk

        role = Role.objects.get(id=pk)
        role.read_only = False
        role.standard = True
        role.save()

        role = Role.objects.get(id=pk)
        self.assertEqual(role.name, "Role One")
        self.assertEqual(role.read_only, True)
        # Can only chang role.standard if nothing else is fiddled with
        # (i.e. atomic?)
        self.assertEqual(role.standard, False)

    def test_cannot_change_name_when_readonly(self):
        role = Role(name="Role One", read_only=True, standard=False)
        role.save()
        pk = role.pk

        role = Role.objects.get(id=pk)
        role.name = "Rick"
        role.save()

        role = Role.objects.get(id=pk)
        self.assertEqual(role.name, "Role One")
        self.assertEqual(role.read_only, True)
        self.assertEqual(role.standard, False)

    def test_can_change_standard_when_readonly(self):
        role = Role(name="Role One", read_only=True, standard=False)
        role.save()
        pk = role.pk

        role = Role.objects.get(id=pk)
        role.standard = True
        role.save()

        role = Role.objects.get(id=pk)
        self.assertEqual(role.name, "Role One")
        self.assertEqual(role.read_only, True)
        self.assertEqual(role.standard, True)

    def test_cant_edit_readonly_name(self):
        role = Role(name="Role One", read_only=True)
        role.save()
        pk = role.pk
        # Try to edit:
        role.name = "Not a womble"
        self.assertFalse(role.save())

        role = Role.objects.get(id=pk)
        self.assertEqual(role.name, "Role One")

    def test_reject_blank(self):
        role = Role(name="")
        self.assertRaises(ValidationError, role.full_clean)

    def test_must_be_unique(self):
        r1 = Role(name="Roller")
        r1.save()

        r2 = Role(name="Roller")
        self.assertRaises(django.db.IntegrityError, r2.save)
