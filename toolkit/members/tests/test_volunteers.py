from __future__ import print_function
import shutil
import os.path
import tempfile
import binascii
import datetime

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.conf import settings

from toolkit.members.models import Member, Volunteer, TrainingRecord
from toolkit.diary.models import Role

from .common import MembersTestsMixin

TINY_VALID_BASE64_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAAXNSR0IArs4c6QAAAARnQU1BA"
    "ACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAMSURBVBhXY/j//z8ABf4C/qc1gYQAAA"
    "AASUVORK5CYII=")


class TestVolunteerListViews(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestVolunteerListViews, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def _test_list_page_common(self, url, include_retired):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Volunteer One")
        self.assertContains(response, "Volunteer Two")
        self.assertContains(response, "Volunteer Three")
        if include_retired:
            self.assertContains(response, "Volunteer Four")
        else:
            self.assertNotContains(response, "Volunteer Four")

        self.assertTemplateUsed(response, "volunteer_list.html")

    def test_list_page_loads_default(self):
        url = reverse("view-volunteer-list")
        self._test_list_page_common(url, include_retired=False)

    def test_list_page_loads_include_inactive(self):
        url = reverse("view-volunteer-list") + "?show-retired=true"
        self._test_list_page_common(url, include_retired=True)

    def test_role_report_loads(self):
        url = reverse("view-volunteer-role-report")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Volunteer One")
        self.assertContains(response, "Volunteer Three")
        # No role assigned:
        self.assertNotContains(response, "Volunteer Two")

        self.assertTemplateUsed(response, "volunteer_role_report.html")


class TestVolunteerEditViews(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestVolunteerEditViews, self).setUp()

        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def test_retire(self):
        v = Volunteer.objects.get(id=1)
        self.assertTrue(v.active)

        url = reverse("inactivate-volunteer")
        response = self.client.post(url, {'volunteer': v.id})

        # Should have deactivated volunteer:
        v = Volunteer.objects.get(id=1)
        self.assertFalse(v.active)

        # And redirected to volunteer list
        self.assertRedirects(response, reverse("view-volunteer-list"))

    def test_unretire(self):
        v = Volunteer.objects.get(id=1)
        v.active = False
        v.save()

        url = reverse("activate-volunteer")
        response = self.client.post(url, {'volunteer': v.id})

        # Shoudl have activated volunteer:
        v = Volunteer.objects.get(id=1)
        self.assertTrue(v.active)

        # And redirected to volunteer list
        self.assertRedirects(response, reverse("view-volunteer-list"))


class TestActivateDeactivateVolunteer(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestActivateDeactivateVolunteer, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def test_load_select_form_retire(self):
        url = reverse("retire-select-volunteer")
        response = self.client.get(url)

        self.assertTemplateUsed(response, 'select_volunteer.html')

        self.assertContains(response, "Volunteer One")
        self.assertContains(response, "Volunteer Two")
        self.assertContains(response, "Volunteer Three")
        self.assertNotContains(response, "Volunteer Four")

    def test_load_select_form_unretire(self):
        url = reverse("unretire-select-volunteer")
        response = self.client.get(url)

        self.assertTemplateUsed(response, 'select_volunteer.html')

        self.assertNotContains(response, "Volunteer One")
        self.assertNotContains(response, "Volunteer Two")
        self.assertNotContains(response, "Volunteer Three")
        self.assertContains(response, "Volunteer Four")

    def test_select_form_post(self):
        url = reverse("unretire-select-volunteer")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)

    def test_retire(self):
        vol = Volunteer.objects.get(id=2)
        self.assertTrue(vol.active)

        url = reverse("inactivate-volunteer")
        response = self.client.post(
            url, data={u"volunteer": u"2"}, follow=True)

        self.assertRedirects(response, reverse("view-volunteer-list"))

        vol = Volunteer.objects.get(id=2)
        self.assertFalse(vol.active)

        self.assertContains(response, u"Retired volunteer Volunteer Two")

    def test_retire_bad_vol_id(self):
        url = reverse("inactivate-volunteer")
        response = self.client.post(url, data={u"volunteer": u"2000"})
        self.assertEqual(response.status_code, 404)

    def test_retire_no_vol_id(self):
        url = reverse("inactivate-volunteer")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_unretire(self):
        vol = Volunteer.objects.get(id=self.vol_4.pk)
        self.assertFalse(vol.active)

        url = reverse("activate-volunteer")
        response = self.client.post(
            url, data={u"volunteer": u"4"}, follow=True)

        self.assertRedirects(response, reverse("view-volunteer-list"))

        vol = Volunteer.objects.get(id=self.vol_4.pk)
        self.assertTrue(vol.active)

        self.assertContains(response, u"Unretired volunteer Volunteer Four")

    def test_unretire_bad_vol_id(self):
        url = reverse("activate-volunteer")
        response = self.client.post(url, data={u"volunteer": u"2000"})
        self.assertEqual(response.status_code, 404)

    def test_unretire_no_vol_id(self):
        url = reverse("activate-volunteer")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class TestVolunteerEdit(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestVolunteerEdit, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))
        self.files_in_use = []

    def tearDown(self):
        for filename in self.files_in_use:
            try:
                if os.path.exists(filename):
                    os.unlink(filename)
            except OSError as ose:
                print("Couldn't delete file!", ose)

    @override_settings(MEDIA_URL="/")
    def test_get_form_edit(self):
        url = reverse("edit-volunteer", kwargs={"volunteer_id": self.vol_1.id})
        response = self.client.get(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        self.assertContains(response, "Volunteer One")
        self.assertContains(response, "volon@cube.test")
        self.assertContains(response, "0800 000 000")
        self.assertContains(response, "1 Road")
        self.assertContains(response, "Town of towns")
        self.assertContains(response, "BS6 123")
        self.assertContains(response, "UKountry")
        self.assertContains(response, "http://1.foo.test/")

        self.assertContains(
            response, "<title>Edit Volunteer Volunteer One</title>")
        self.assertContains(response,
                            '<a href="/tmp/path/to/portrait">',
                            html=False)

    def test_get_form_add(self):
        url = reverse("add-volunteer")
        response = self.client.get(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        self.assertContains(
            response, "<title>Add Volunteer</title>", html=True)
        # Should have default mugshot:
        self.assertContains(
            response,
            '<img id="photo" alt="No photo yet" src="{0}" width="75">'
            .format(settings.DEFAULT_MUGSHOT),
            html=True)

    def test_get_form_edit_invalid_vol(self):
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 10001})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_new_vol_minimal_data(self):
        init_vol_count = Volunteer.objects.count()
        init_mem_count = Member.objects.count()

        url = reverse("add-volunteer")
        response = self.client.post(url, data={
            u'mem-name': u'New Volunteer, called \u0187hri\u01a8topher'
        }, follow=True)
        self.assertRedirects(response, reverse("view-volunteer-summary"))

        self.assertContains(
            response,
            u'<li class="success">Created volunteer &#39;New Volunteer, '
            u'called \u0187hri\u01a8topher&#39;</li>',
            html=True
        )

        # one more of each:
        self.assertEqual(Volunteer.objects.count(), init_vol_count + 1)
        self.assertEqual(Member.objects.count(), init_mem_count + 1)

        # New things:
        new_member = Member.objects.get(
            name=u"New Volunteer, called \u0187hri\u01a8topher")
        # Implicitly check Volunteer record exists:
        self.assertTrue(new_member.volunteer.active)

    def test_post_new_vol_all_data(self):
        init_vol_count = Volunteer.objects.count()
        init_mem_count = Member.objects.count()

        url = reverse("add-volunteer")
        response = self.client.post(url, data={
            u'mem-name': u'Another New Volunteer',
            u'mem-email': 'snoo@whatver.com',
            u'mem-address': "somewhere over the rainbow, I guess",
            u'mem-posttown': "Town Town Town!",
            u'mem-postcode': "< Sixteen chars?",
            u'mem-country': "Suriname",
            u'mem-website': "http://still_don't_care/",
            u'mem-phone': "+44 1000000000000001",
            u'mem-altphone': "-1 3202394 2352 23 234",
            u'mem-mailout_failed': "t",
            u'mem-notes': "member notes shouldn't be on this form!",
            u'vol-notes': "plays the balalaika really badly",
            u'vol-roles': [2, 3],
        }, follow=True)

        self.assertRedirects(response, reverse("view-volunteer-summary"))

        self.assertContains(
            response,
            u'<li class="success">Created volunteer &#39;Another New '
            u'Volunteer&#39;</li>',
            html=True
        )

        # one more of each:
        self.assertEqual(Volunteer.objects.count(), init_vol_count + 1)
        self.assertEqual(Member.objects.count(), init_mem_count + 1)

        # New things:
        new_member = Member.objects.get(name=u"Another New Volunteer")
        self.assertEqual(new_member.email, 'snoo@whatver.com')
        self.assertEqual(new_member.address,
                         "somewhere over the rainbow, I guess")
        self.assertEqual(new_member.posttown, "Town Town Town!")
        self.assertEqual(new_member.postcode, "< Sixteen chars?")
        self.assertEqual(new_member.country, "Suriname")
        self.assertEqual(new_member.website, "http://still_don't_care/")
        self.assertEqual(new_member.phone, "+44 1000000000000001")
        self.assertEqual(new_member.altphone, "-1 3202394 2352 23 234")
        self.assertFalse(new_member.mailout)
        # not in form, shouldn't have changed:
        self.assertFalse(new_member.mailout_failed)
        self.assertTrue(new_member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(new_member.notes, '')

        self.assertTrue(new_member.volunteer.active)
        self.assertEqual(new_member.volunteer.notes,
                         "plays the balalaika really badly")

        roles = new_member.volunteer.roles.all()

        self.assertEqual(len(roles), 2)
        self.assertEqual(roles[0].id, 2)
        self.assertEqual(roles[1].id, 3)

    def test_post_new_vol_invalid_missing_data(self):
        url = reverse("add-volunteer")
        response = self.client.post(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        # The only mandatory field (!)
        self.assertFormError(response, 'mem_form', 'name',
                             u'This field is required.')

    def test_post_edit_vol_minimal_data(self):
        init_vol_count = Volunteer.objects.count()
        init_mem_count = Member.objects.count()

        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={
            u'mem-name': u'Renam\u018fd Vol'
        }, follow=True)
        self.assertRedirects(response, reverse("view-volunteer-summary"))

        self.assertContains(
            response,
            u'<li class="success">Updated volunteer &#39;Renam\u018fd '
            u'Vol&#39;</li>',
            html=True
        )

        # same number of each:
        self.assertEqual(Volunteer.objects.count(), init_vol_count)
        self.assertEqual(Member.objects.count(), init_mem_count)

        # extant member
        volunteer = Volunteer.objects.get(id=1)
        member = volunteer.member
        self.assertTrue(member.volunteer.active)
        # Changed things:
        self.assertEqual(member.name, u"Renam\u018fd Vol")
        self.assertEqual(member.email, "")
        self.assertEqual(member.address, "")
        self.assertEqual(member.posttown, "")
        self.assertEqual(member.postcode, "")
        self.assertEqual(member.country, "")
        self.assertEqual(member.website, "")
        self.assertEqual(member.phone, "")
        self.assertEqual(member.altphone, "")
        self.assertFalse(member.mailout)
        self.assertFalse(member.mailout_failed)
        self.assertTrue(member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(member.notes, '')

        self.assertTrue(member.volunteer.active)
        self.assertEqual(member.volunteer.notes, "")
        # Won't have changed without "clear" being checked:
        self.assertEqual(member.volunteer.portrait, '/tmp/path/to/portrait')

        self.assertEqual(member.volunteer.roles.count(), 0)

    def test_post_edit_vol_all_data(self):
        init_vol_count = Volunteer.objects.count()
        init_mem_count = Member.objects.count()

        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})

        response = self.client.post(url, data={
            u'mem-name': u'Renam\u018fd Vol',
            u'mem-email': 'snoo@whatver.com',
            u'mem-address': "somewhere over the rainbow, I guess",
            u'mem-posttown': "Town Town Town!",
            u'mem-postcode': "< Sixteen chars?",
            u'mem-country': "Suriname",
            u'mem-website': "http://still_don't_care/",
            u'mem-phone': "+44 1000000000000001",
            u'mem-altphone': "-1 3202394 2352 23 234",
            u'mem-mailout_failed': "t",
            u'mem-notes': "member notes shouldn't be on this form!",
            u'vol-notes': "plays the balalaika really badly",
            u'vol-roles': [2, 3],
        }, follow=True)

        self.assertRedirects(response, reverse("view-volunteer-summary"))

        self.assertContains(
            response,
            u'<li class="success">Updated volunteer &#39;Renam\u018fd '
            u'Vol&#39;</li>',
            html=True
        )

        # same number of each:
        self.assertEqual(Volunteer.objects.count(), init_vol_count)
        self.assertEqual(Member.objects.count(), init_mem_count)

        # extant member
        volunteer = Volunteer.objects.get(id=1)
        member = volunteer.member
        self.assertTrue(member.volunteer.active)
        self.assertEqual(member.name, u"Renam\u018fd Vol")
        self.assertEqual(member.email, 'snoo@whatver.com')
        self.assertEqual(member.address, "somewhere over the rainbow, I guess")
        self.assertEqual(member.posttown, "Town Town Town!")
        self.assertEqual(member.postcode, "< Sixteen chars?")
        self.assertEqual(member.country, "Suriname")
        self.assertEqual(member.website, "http://still_don't_care/")
        self.assertEqual(member.phone, "+44 1000000000000001")
        self.assertEqual(member.altphone, "-1 3202394 2352 23 234")
        self.assertFalse(member.mailout)
        # not in form, shouldn't have changed:
        self.assertFalse(member.mailout_failed)
        self.assertTrue(member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(member.notes, '')

        self.assertTrue(member.volunteer.active)
        self.assertEqual(member.volunteer.notes,
                         "plays the balalaika really badly")

        roles = member.volunteer.roles.all()

        self.assertEqual(len(roles), 2)
        self.assertEqual(roles[0].id, 2)
        self.assertEqual(roles[1].id, 3)

    def test_post_update_vol_invalid_missing_data(self):
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        # The only mandatory field (!)
        self.assertFormError(response, 'mem_form', 'name',
                             u'This field is required.')

    def test_post_update_vol_invalid_vol_id(self):
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 10001})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_update_vol_clear_portrait(self):

        temp_jpg = tempfile.NamedTemporaryFile(
            dir="/tmp", prefix="toolkit-test-", suffix=".jpg", delete=False)

        # Ensure files get cleaned up:
        self.files_in_use.append(temp_jpg.name)

        temp_jpg.close()

        # Add to vol 1:
        vol = Volunteer.objects.get(id=1)
        vol.portrait = temp_jpg.name
        vol.save()

        # No errant code should have deleted the files:
        self.assertTrue(os.path.isfile(temp_jpg.name))

        # Post an edit to clear the image:
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={
            u'mem-name': u'Pictureless Person',
            u'vol-portrait-clear': 't',
        })
        self.assertRedirects(response, reverse("view-volunteer-summary"))

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(vol.member.name, u'Pictureless Person')
        self.assertEqual(vol.portrait, '')

        # Should have deleted the old images:
        self.assertFalse(os.path.isfile(temp_jpg.name))

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_update_vol_change_portrait_success(self):
        temp_old_jpg = tempfile.NamedTemporaryFile(
            dir="/tmp", prefix="toolkit-test-", suffix=".jpg", delete=False)

        expected_upload_path = os.path.join(
            '/tmp', settings.VOLUNTEER_PORTRAIT_DIR, "image_bluesq.jpg")

        # Ensure files get cleaned up:
        self.files_in_use.append(temp_old_jpg.name)
        self.files_in_use.append(expected_upload_path)
        temp_old_jpg.close()

        # Add to vol 1:
        vol = Volunteer.objects.get(id=1)
        vol.portrait = temp_old_jpg.name
        vol.save()

        # No errant code should have deleted the files:
        self.assertTrue(os.path.isfile(temp_old_jpg.name))

        # Get new image to send:
        new_jpg_filename = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "test_data", "image_bluesq.jpg")

        with open(new_jpg_filename, "rb") as new_jpg_file:
            # Post an edit to update the image:
            url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
            response = self.client.post(url, data={
                u'mem-name': u'Pictureless Person',
                u'vol-portrait': new_jpg_file,
            })

        self.assertRedirects(response, reverse("view-volunteer-summary"))

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(vol.member.name, u'Pictureless Person')

        # Portrait path should be:
        self.assertEqual(vol.portrait.name, os.path.join(
            settings.VOLUNTEER_PORTRAIT_DIR, "image_bluesq.jpg"))
        # And should have 'uploaded' file to:
        self.assertTrue(os.path.isfile(expected_upload_path))

        # Should have deleted the old images:
        self.assertFalse(os.path.isfile(temp_old_jpg.name))

        # TODO do this properly:
        shutil.rmtree(os.path.join('/tmp', settings.VOLUNTEER_PORTRAIT_DIR))

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_update_vol_set_portrait_data_uri(self):
        expected_upload_path = os.path.join(
            settings.VOLUNTEER_PORTRAIT_DIR, "webcam_photo.png")
        expected_upload_location = os.path.join('/tmp', expected_upload_path)

        # Ensure files get cleaned up:
        self.files_in_use.append(expected_upload_location)

        # Add to vol 1:
        vol = Volunteer.objects.get(id=1)
        self.assertNotEqual(vol.portrait, expected_upload_path)

        # Post an edit to update the image:
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={
            u'mem-name': u'Pictureless Person',
            u'vol-image_data': ("data:image/png;base64,%s"
                                % TINY_VALID_BASE64_PNG)
        })

        self.assertRedirects(response, reverse("view-volunteer-summary"))

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(vol.member.name, u'Pictureless Person')

        # Portrait path should be:
        self.assertEqual(vol.portrait.name, expected_upload_path)
        # And should have 'uploaded' file to:
        self.assertTrue(os.path.isfile(expected_upload_location))
        # And contents:
        with open(expected_upload_location, "rb") as imgf:
            self.assertEqual(
                imgf.read(), binascii.a2b_base64(TINY_VALID_BASE64_PNG))

        # TODO do this properly!
        shutil.rmtree(os.path.join('/tmp', settings.VOLUNTEER_PORTRAIT_DIR))

    def test_post_update_vol_set_portrait_data_uri_bad_mimetype(self):
        vol = Volunteer.objects.get(id=1)
        initial_portrait = vol.portrait.name
        self.assertNotEqual(initial_portrait, None)

        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={
            u'mem-name': u'Pictureless Person',
            u'vol-image_data': ("data:image/jpeg;base64,%s"
                                % TINY_VALID_BASE64_PNG)
        })

        self.assertTemplateUsed(response, "form_volunteer.html")
        # * No form error, as it's a form-wide validation fail, not per-field.
        #   Settle for just being happy that the file hasn't been saved
        # self.assertFormError(response, 'vol_form', 'image_data',
        #                      u'Image data format not recognised')

        vol = Volunteer.objects.get(id=1)
        self.assertNotEqual(vol.member.name, u'Pictureless Person')
        self.assertEqual(vol.portrait.name, initial_portrait)

    def test_post_update_vol_set_portrait_data_bad_bytes(self):
        vol = Volunteer.objects.get(id=1)
        initial_portrait = vol.portrait.name
        self.assertNotEqual(initial_portrait, None)

        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        INVALID_PNG = "Spinach" + TINY_VALID_BASE64_PNG
        response = self.client.post(url, data={
            u'mem-name': u'Pictureless Person',
            u'vol-image_data': "data:image/png;base64,%s" % INVALID_PNG,
        })

        self.assertTemplateUsed(response, "form_volunteer.html")
        # * No form error, as it's a form-wide validation fail, not per-field.
        #   Settle for just being happy that the file hasn't been saved
        # self.assertFormError(response, 'vol_form', 'image_data',
        #                      u'Image data format not recognised')

        vol = Volunteer.objects.get(id=1)
        self.assertNotEqual(vol.member.name, u'Pictureless Person')
        self.assertEqual(vol.portrait.name, initial_portrait)


class TestAddTraining(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestAddTraining, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def _test_add_training_common(self, is_general):
        url = reverse("add-volunteer-training-record",
                      kwargs={"volunteer_id": 1})
        role = Role.objects.get(id=2)
        vol = Volunteer.objects.get(id=1)

        self.assertFalse(role in vol.roles.all())

        trainer = u"Friendly Trainer \u0187hri\u01a8topher"
        notes = u" No notes\nare noted... here. "

        post_data={
            'training-training_type': TrainingRecord.ROLE_TRAINING,
            'training-trainer': trainer,
            'training-training_date': "1/2/2015",
            'training-notes':  notes
        }
        if is_general:
            post_data['training-training_type'] = \
                    TrainingRecord.GENERAL_TRAINING
            post_data['training-role'] = ""
        else:
            post_data['training-training_type'] = TrainingRecord.ROLE_TRAINING
            post_data['training-role'] = role.id

        response = self.client.post(url, data=post_data)
        expected = {
            "succeeded": True,
            "id": 1,
            "training_description": str(role),
            "training_date": "01/02/2015",
            "trainer": trainer,
            "notes": notes.strip()
        }
        if is_general:
            expected['training_description'] = \
                TrainingRecord.GENERAL_TRAINING_DESC
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(len(vol.training_records.all()), 1)
        record = vol.training_records.all()[0]
        self.assertEqual(record.role, None if is_general else role)
        self.assertEqual(record.trainer, trainer)
        self.assertEqual(record.notes, notes.strip())
        self.assertEqual(record.training_date,
                         datetime.date(day=1, month=2, year=2015))
        if is_general:
            self.assertFalse(role in vol.roles.all())
        else:
            self.assertTrue(role in vol.roles.all())

    def test_add_role_training(self):
        self._test_add_training_common(is_general=False)

    def test_add_general_training(self):
        self._test_add_training_common(is_general=True)

    def test_add_training_missing_training_type_data(self):
        url = reverse("add-volunteer-training-record",
                      kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "succeeded": False,
            "errors": {
                u'training_type': [u'This field is required.'],
                u'trainer': [u'This field is required.'],
                u'training_date': [u'This field is required.'],
            }
        })
        vol = Volunteer.objects.get(id=1)
        self.assertEqual(len(vol.training_records.all()), 0)

    def test_add_training_missing_role(self):
        url = reverse("add-volunteer-training-record",
                      kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={
            'training-training_type': TrainingRecord.ROLE_TRAINING,
            'training-trainer': "trainer",
            'training-training_date': "1/2/2015",
            'training-notes':  "notes"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            "succeeded": False,
            "errors": {
                u'role': [u'This field is required.'],
            }
        }, response.json())
        vol = Volunteer.objects.get(id=1)
        self.assertEqual(len(vol.training_records.all()), 0)

    def test_add_training_inactive_volunteer(self):
        vol = Volunteer.objects.filter(active=False)[0]
        url = reverse("add-volunteer-training-record",
                      kwargs={"volunteer_id": vol.id})
        response = self.client.post(url, data={
            'training-role': 1,
            'training-trainer': "Trainer",
            'training-training_date': "1/2/2015",
            'training-notes':  None
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "succeeded": False,
            "errors": "volunteer is not active"
        })
        self.assertEqual(len(vol.training_records.all()), 0)


class TestDeleteTraining(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestDeleteTraining, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def test_delete_training_record(self):
        vol = Volunteer.objects.get(id=1)
        role = Role.objects.get(id=1)

        record = TrainingRecord(
            volunteer=vol,
            training_type=TrainingRecord.ROLE_TRAINING,
            role=role,
            trainer="Trainer",
            training_date=datetime.date(day=29, month=2, year=2012),
        )
        record.save()

        url = reverse("delete-volunteer-training-record",
                      kwargs={"training_record_id": record.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/plain")
        self.assertEqual(response.content, b"OK")

        self.assertEqual(len(TrainingRecord.objects.all()), 0)

    def test_delete_training_record_inactive_vol(self):
        vol = Volunteer.objects.get(id=1)
        role = Role.objects.get(id=1)

        record = TrainingRecord(
            volunteer=vol,
            training_type=TrainingRecord.ROLE_TRAINING,
            role=role,
            trainer="Trainer",
            training_date=datetime.date(day=29, month=2, year=2012),
        )
        record.save()

        vol.active = False
        vol.save()

        url = reverse("delete-volunteer-training-record",
                      kwargs={"training_record_id": record.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(len(TrainingRecord.objects.all()), 1)


class TestAddGroupTraining(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestAddGroupTraining, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def test_get_form(self):
        url = reverse("add-volunteer-training-group-record")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "form_group_training.html")

    def _shared_test_add_group_role_record(self, test_general):
        url = reverse("add-volunteer-training-group-record")

        role = Role.objects.get(id=1)
        trainer = u"Trainer \u0187hri\u01a8topher"
        notes = u" Some not\u018fs\nwere noted here. "
        training_date = datetime.date(day=4, month=5, year=2016)

        volunteers = Volunteer.objects.filter(active=True)[:3]
        self.assertEqual(len(volunteers), 3)
        post_data = {
            "role": "",
            "trainer": trainer,
            "training_date": "4/5/2016",
            "notes": notes,
            "volunteers": [v.member.id for v in volunteers]
        }

        if test_general:
            post_data["type"] = TrainingRecord.GENERAL_TRAINING
        else:
            post_data["type"] = TrainingRecord.ROLE_TRAINING
            post_data["role"] = role.id

        response = self.client.post(url, data=post_data)
        self.assertRedirects(response, url)

        volunteers = Volunteer.objects.filter(active=True)[:3]
        for vol in volunteers:
            recs = vol.training_records.all()
            self.assertEqual(len(recs), 1)
            if test_general:
                self.assertEqual(recs[0].training_type,
                                 TrainingRecord.GENERAL_TRAINING)
                self.assertEqual(recs[0].role, None)
            else:
                self.assertTrue(role in vol.roles.all())
                self.assertEqual(recs[0].training_type,
                                 TrainingRecord.ROLE_TRAINING)
                self.assertEqual(recs[0].role, role)
            self.assertEqual(recs[0].notes, notes.strip())
            self.assertEqual(recs[0].trainer, trainer)
            self.assertEqual(recs[0].training_date, training_date)

    def test_add_group_role_record(self):
        self._shared_test_add_group_role_record(test_general=False)

    def test_add_group_general_record(self):
        self._shared_test_add_group_role_record(test_general=True)

    def test_add_group_inactive_volunteer(self):
        url = reverse("add-volunteer-training-group-record")

        role = Role.objects.get(id=1)

        volunteers = Volunteer.objects.filter(active=True)[:3]
        self.assertEqual(len(volunteers), 3)
        volunteers[1].active = False
        volunteers[1].save()

        response = self.client.post(url, data={
            "type": TrainingRecord.ROLE_TRAINING,
            "role": role.id,
            "trainer": "trainer",
            "training_date": "4/5/2016",
            "notes": "",
            "volunteers": [v.member.id for v in volunteers]
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_group_training.html")

        # It's not the ideal error message, I grant you:
        self.assertFormError(
            response, 'form', 'volunteers',
            u'Select a valid choice. %d is not one of the available choices.'
            % (volunteers[1].member.id))

    def test_add_group_record_missing_data(self):
        url = reverse("add-volunteer-training-group-record")

        self.assertEqual(len(TrainingRecord.objects.all()), 0)

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_group_training.html")

        self.assertFormError(response, 'form', 'type',
                             u'This field is required.')
        # 'role' isn't requireed unless 'type' is selected
        #self.assertFormError(response, 'form', 'role',
        #                     u'This field is required.')
        self.assertFormError(response, 'form', 'training_date',
                             u'This field is required.')
        self.assertFormError(response, 'form', 'trainer',
                             u'This field is required.')
        self.assertFormError(response, 'form', 'volunteers',
                             u'This field is required.')

    def test_add_group_record_missing_role(self):
        url = reverse("add-volunteer-training-group-record")

        self.assertEqual(len(TrainingRecord.objects.all()), 0)

        response = self.client.post(url, data={
            "type": TrainingRecord.ROLE_TRAINING,
            "trainer": "trainer",
            "training_date": "4/5/2016",
            "notes": "",
            "volunteers": 1
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_group_training.html")

        self.assertFormError(response, 'form', 'role',
                             u'This field is required.')




class TestViewVolunteerTraining(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestViewVolunteerTraining, self).setUp()
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def test_content(self):
        url = reverse("view-volunteer-training-report")

        volunteers = Volunteer.objects.filter(active=True)[:3]
        self.assertEqual(len(volunteers), 3)

        role = Role.objects.get(id=1)
        training_date = datetime.date(day=4, month=5, year=2016)

        for vol in volunteers:
            self.assertTrue(vol.active)
            vol.roles.add(role)
            record = TrainingRecord(
                volunteer=vol, training_type=TrainingRecord.ROLE_TRAINING,
                role=role, trainer="trainer", training_date=training_date)
            record.save()

        # Add a second, older record, that should not take precedence, for
        # vol[0]
        newer_date = training_date - datetime.timedelta(days=1)
        new_record = TrainingRecord(
            volunteer=volunteers[0],
            training_type=TrainingRecord.ROLE_TRAINING, role=role,
            trainer="trainer", training_date=newer_date)
        new_record.save()

        # Add a third old record, that should also not take
        # precedence, for vol[0] (to force coverage of one of the
        # conditionals in the view...)
        newer_date = training_date - datetime.timedelta(days=1)
        new_record = TrainingRecord(
            volunteer=volunteers[0],
            training_type=TrainingRecord.ROLE_TRAINING, role=role,
            trainer="trainer", training_date=newer_date)
        new_record.save()

        # Similarly, add an older and a newer general training record for vol
        # 3:
        older_date = training_date - datetime.timedelta(days=2)
        new_record = TrainingRecord(
            volunteer=volunteers[2],
            training_type=TrainingRecord.GENERAL_TRAINING,
            trainer="old trainer", training_date=older_date)
        new_record.save()

        newer_date = training_date - datetime.timedelta(days=1)
        new_record = TrainingRecord(
            volunteer=volunteers[2],
            training_type=TrainingRecord.GENERAL_TRAINING,
            trainer="new trainer", training_date=newer_date)
        new_record.save()

        # Make vol[1] inactive
        volunteers[1].active = False
        volunteers[1].save()

        # Make vol[2] not have the role:
        volunteers[2].roles.remove(role)

        # ...so should just have one training record:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "volunteer_training_report.html")
        self.assertContains(response, """
            <div class="role_info" id="id_role_info_1">
              <h2>Role 1 (standard)</h2>
              <ul>

                  <li class="training_record" data-training-time="1462316400">
                    <a href="/volunteers/1/edit#training-record">
                      Volunteer One
                    </a>
                    &mdash; last trained 04/05/2016
                  </li>

              </ul>
            </div>""", html=True)
        self.assertNotContains(response, "Role 2")
        self.assertContains(response,"""
            <div>
              <h2>General Safety Training</h2>
              <ul>
                  <li class="training_record" data-training-time="0">
                    <a href="/volunteers/1/edit">
                      Volunteer One
                    </a>
                    &mdash; never trained
                  </li>
                  <li class="training_record" data-training-time="1462230000">
                    <a href="/volunteers/3/edit">
                      Volunteer Three
                    </a>
                    &mdash;
                        last trained 03/05/2016
                  </li>
              </ul>
            </div>""", html=True)

        self.assertNotContains(response, "Volunteer Two")
        self.assertNotContains(response, "Volunteer Four")

    def test_no_post(self):
        url = reverse("view-volunteer-training-report")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
