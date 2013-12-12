import shutil
import urllib
import os.path
import tempfile
import smtplib
import email.parser
import email.header

from mock import patch, call

from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from toolkit.members.models import Member, Volunteer
from toolkit.diary.models import Role
import toolkit.members.tasks


class MembersTestsMixin(object):

    def setUp(self):
        self._setup_test_data()

        return super(MembersTestsMixin, self).setUp()

    def _setup_test_data(self):
        # Roles:
        r1 = Role(name="Role 1 (standard)", read_only=False, standard=True)
        r1.save()
        r2 = Role(name="Role 2 (nonstandard)", read_only=False, standard=False)
        r2.save()
        r3 = Role(name="Role 3", read_only=False, standard=False)
        r3.save()

        # Members:
        self.mem_1 = Member(name=u"Member On\u0205", email="one@example.com", number="1", postcode="BS1 1AA")
        self.mem_1.save()
        self.mem_2 = Member(name=u"Tw\u020d Member", email="two@example.com", number="02", postcode="")
        self.mem_2.save()
        self.mem_3 = Member(name=u"Some Third Chap", email="two@member.test", number="000", postcode="NORAD")
        self.mem_3.save()
        self.mem_4 = Member(name="Volunteer One", email="volon@cube.test", number="3",
                            phone="0800 000 000", address="1 Road", posttown="Town of towns", postcode="BS6 123",
                            country="UKountry", website="http://1.foo.test/")
        self.mem_4.save()
        self.mem_5 = Member(name="Volunteer Two", email="", number="4",
                            phone="", altphone="", address="", posttown="", postcode="", country="",
                            website="http://two.foo.test/")
        self.mem_5.save()
        self.mem_6 = Member(name="Volunteer Three", email="volthree@foo.test", number="4",
                            phone="", altphone="", address="", posttown="", postcode="", country="",
                            website="")
        self.mem_6.save()
        self.mem_7 = Member(name="Volunteer Four", email="four4@foo.test", number="o4",
                            phone="", altphone="", address="", posttown="", postcode="", country="",
                            website="")
        self.mem_7.save()
        self.mem_8 = Member(name=u"Number Eight, No mailout please", email="bart@bart.test", number="010", mailout=False)
        self.mem_8.save()
        self.mem_8 = Member(name=u"Number Nine, mailout failed", email="frobney@squoo.test", number="010", mailout_failed=True)
        self.mem_8.save()

        # Volunteers:
        self.vol_1 = Volunteer(
            member=self.mem_4, notes=u'Likes the $, the \u00a3 and the \u20ac',
            portrait=settings.MEDIA_ROOT + "/path/to/portrait"
        )
        self.vol_1.save()
        self.vol_1.roles = [r1, r3]
        self.vol_1.save()

        self.vol_2 = Volunteer(member=self.mem_5)
        self.vol_2.save()

        self.vol_3 = Volunteer(member=self.mem_6)
        self.vol_3.save()
        self.vol_3.roles = [r3]
        self.vol_3.save()

        self.vol_4 = Volunteer(member=self.mem_7, active=False, notes=u"Subliminal, superluminous")
        self.vol_4.save()
        self.vol_4.roles = [r3]
        self.vol_4.save()

        # System user:
        user_rw = auth_models.User.objects.create_user('admin', 'toolkit_admin@localhost', 'T3stPassword!')
        # Create dummy ContentType:
        ct = contenttypes.models.ContentType.objects.get_or_create(
            model='',
            app_label='toolkit'
        )[0]
        # Create 'write' permission:
        write_permission = auth_models.Permission.objects.get_or_create(
            name='Write access to all toolkit content',
            content_type=ct,
            codename='write'
        )[0]
        # Give "admin" user the write permission:
        user_rw.user_permissions.add(write_permission)


class SecurityTests(MembersTestsMixin, TestCase):

    """Basic test that the private pages do not load without a login"""

    def test_private_urls(self):
        """All URLs which should 302 redirect to the login page"""
        views_to_test = {
            # Volunteer urls:
            'add-volunteer': {},
            'view-volunteer-list': {},
            'unretire-select-volunteer': {},
            'retire-select-volunteer': {},
            'edit-volunteer': {'volunteer_id': 1},
            'activate-volunteer': {},
            'inactivate-volunteer': {},
            # Member urls:
            'add-member': {},
            'search-members': {},
            'view-member': {'member_id': 1},
            'edit-member': {'member_id': 1},
            'delete-member': {'member_id': 1},
            'member-statistics': {},
        }
        for view_name, kwargs in views_to_test.iteritems():
            url = reverse(view_name, kwargs=kwargs)
            expected_redirect = "{0}?next={1}".format(reverse("django.contrib.auth.views.login"), url)

            # Test GET:
            response = self.client.get(url)
            self.assertRedirects(response, expected_redirect)

            # Test POST:
            response = self.client.post(url)
            self.assertRedirects(response, expected_redirect)

    def test_protected_urls(self):
        """URLs which should only work if the member key is knonw"""

        views_to_test = (
            'edit-member',
            'unsubscribe-member',
        )

        member = Member.objects.get(id=1)

        # First try without a key:
        for view_name in views_to_test:
            url = reverse(view_name, kwargs={'member_id': member.id})
            expected_redirect = "{0}?next={1}".format(reverse("django.contrib.auth.views.login"), url)

            # Test GET:
            response = self.client.get(url)
            self.assertRedirects(response, expected_redirect)

            # Test POST:
            response = self.client.post(url)
            self.assertRedirects(response, expected_redirect)

        # Now try with the key:
        for view_name in views_to_test:
            url = "{0}?k={1}".format(
                reverse(view_name, kwargs={'member_id': member.id}),
                member.mailout_key)
            # Test GET:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, member.name)


class TestMemberModelManager(MembersTestsMixin, TestCase):
    def test_email_recipients(self):
        recipients = Member.objects.mailout_recipients()
        self.assertEqual(recipients.count(), 6)
        for member in recipients:
            self.assertTrue(member.mailout)
            self.assertFalse(member.mailout_failed)
            self.assertTrue(member.email)

class TestVolunteerEditViews(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestVolunteerEditViews, self).setUp()

        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

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


class TestAddMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestAddMemberView, self).setUp()

        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def test_get_form(self):
        url = reverse("add-member")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_member.html")

    def test_post_form(self):
        new_name = u"Some New \u20acejit"

        self.assertEqual(Member.objects.filter(name=new_name).count(), 0)

        url = reverse("add-member")
        response = self.client.post(url, data={
            u"name": new_name,
            u"email": u"blah.blah-blah@hard-to-tell-if-genuine.uk",
            u"postcode": "SW1A 1AA",
        }, follow=True)

        self.assertRedirects(response, url)
        self.assertTemplateUsed(response, "form_new_member.html")

        member = Member.objects.get(name=new_name)
        self.assertEqual(member.email, u"blah.blah-blah@hard-to-tell-if-genuine.uk")
        self.assertEqual(member.postcode, u"SW1A 1AA")

        self.assertContains(response, u"Added member: {0}".format(member.number))

    def test_post_form_invalid_data_missing(self):
        url = reverse("add-member")
        response = self.client.post(url)

        count_before = Member.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_member.html")

        self.assertFormError(response, 'form', 'name', u'This field is required.')

        self.assertEqual(count_before, Member.objects.count())

    def test_invalid_method(self):
        url = reverse("add-member")
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)


class TestSearchMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestSearchMemberView, self).setUp()

        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    @patch('toolkit.members.member_views.Member')
    def test_no_query(self, member_patch):
        url = reverse("search-members")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members.html")

        self.assertFalse(member_patch.objects.filter.called)

    def test_query_with_results(self):
        url = reverse("search-members")
        response = self.client.get(url, data={'q': u'member'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")

        self.assertContains(response, u"<td>Member On\u0205</td>", html=True)
        self.assertContains(response, u'<a href="mailto:one@example.com">one@example.com</a>', html=True)
        self.assertContains(response, u"<td>BS1 1AA</td>", html=True)

        self.assertContains(response, u"<td>Tw\u020d Member</td>", html=True)
        self.assertContains(response, u'<a href="mailto:two@example.com">two@example.com</a>', html=True)

        self.assertContains(response, u"<td>Some Third Chap</td>", html=True)
        self.assertContains(response, u'<td><a href="mailto:two@member.test">two@member.test</a></td>', html=True)
        self.assertContains(response, u"<td>NORAD</td>", html=True)

        # Shouldn't have Edit / Delete buttons:
        self.assertNotContains(response, u'<input type="submit" value="Edit">', html=True)
        self.assertNotContains(response, u'<input type="submit" value="Delete">', html=True)

    def test_query_no_results(self):
        url = reverse("search-members")

        response = self.client.get(url, data={'q': u'toast'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")

    def test_query_with_edit_link(self):
        url = reverse("search-members")
        response = self.client.get(url, data={
            'q': u'third chap',
            'show_edit_link': u't',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")

        self.assertContains(
            response,
            u'<form method="get" action="{0}"><input type="submit" value="Edit"></form>'.format(
                reverse("edit-member", kwargs={"member_id": 3})
            ),
            html=True,
        )
        self.assertNotContains(response, u'<input type="submit" value="Delete">', html=True)

    def test_query_with_delete_link(self):
        url = reverse("search-members")
        response = self.client.get(url, data={
            'q': u'third chap',
            'show_delete_link': u't',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")

        self.assertContains(response,
                            u'<input type="submit" value="Delete">',
                            html=True,
                            )

        self.assertContains(response,
                            reverse("delete-member", kwargs={"member_id": 3})
                            )
        self.assertNotContains(response, u'<input type="submit" value="Edit">', html=True)


class TestDeleteMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestDeleteMemberView, self).setUp()

        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    def test_delete(self):
        self.assertEqual(Member.objects.filter(id=1).count(), 1)

        url = reverse("delete-member", kwargs={"member_id": 1})
        response = self.client.post(url, follow=True)

        self.assertRedirects(response, reverse("search-members"))
        self.assertContains(response, u"Deleted member: 1 (Member On\u0205)")

        self.assertEqual(Member.objects.filter(id=1).count(), 0)

    def test_delete_nonexistent(self):
        url = reverse("delete-member", kwargs={"member_id": 1000})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_not_allowed(self):
        self.assertEqual(Member.objects.filter(id=1).count(), 1)

        url = reverse("delete-member", kwargs={"member_id": 1})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Member.objects.filter(id=1).count(), 1)


class TestEditMemberViewNotLoggedIn(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestEditMemberViewNotLoggedIn, self).setUp()

    def _assert_redirect_to_login(self, response, url, extra_parameters=""):
        expected_redirect = (
            reverse("login") +
            "?next=" +
            urllib.quote(url + extra_parameters)
        )
        self.assertRedirects(response, expected_redirect)

    # GET tests ###########################################
    def test_edit_get_form(self):
        member = Member.objects.get(pk=2)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(url, data={
            'k': member.mailout_key,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

    def test_edit_get_form_no_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(url)

        self._assert_redirect_to_login(response, url)

    def test_edit_get_form_incorrect_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(url, data={
            'k': "the WRONG KEY",
        })
        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

    def test_edit_get_form_invalid_memberid(self):
        url = reverse("edit-member", kwargs={"member_id": 21212})
        response = self.client.get(url, data={
            'k': "the WRONG KEY",
        })
        # If the member doesn't exist then don't give a specific error to that
        # effect, just redirect to the login page:
        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

    # POST tests ###########################################
    def test_edit_post_form_minimal_data(self):
        new_name = u'N\u018EW Name'

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, u"Tw\u020d Member")
        member_mailout_key = member.mailout_key
        self.assertTrue(member.is_member)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'name': new_name,
            'k': member_mailout_key,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, new_name)
        self.assertEqual(member.email, "")
        self.assertEqual(member.address, "")
        self.assertEqual(member.posttown, "")
        self.assertEqual(member.postcode, "")
        self.assertEqual(member.country, "")
        self.assertEqual(member.website, "")
        self.assertEqual(member.phone, "")
        self.assertEqual(member.altphone, "")
        self.assertEqual(member.notes, "")
        self.assertFalse(member.mailout)
        self.assertFalse(member.mailout_failed)
        self.assertFalse(member.is_member)

        # Shouldn't have been changed:
        self.assertEqual(member.mailout_key, member_mailout_key)

        self.assertContains(response, new_name)
        self.assertContains(response, "Member 02 updated")

    def test_edit_post_form_all_data(self):
        new_name = u'N\u018EW Name'

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, u"Tw\u020d Member")
        member_mailout_key = member.mailout_key
        self.assertTrue(member.is_member)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'name': new_name,
            'email': 'snoo@whatver',
            'k': member_mailout_key,
            'address': "somewhere over the rainbow, I guess",
            'posttown': "Town Town Town!",
            'postcode': "< Sixteen chars?",
            'country': "Suriname",
            'website': "http://don't_care/",
            'phone': "+44 0000000000000001",
            'altphone': "-1 3202394 2352 23 234",
            'notes': "plays the balalaika really badly",
            'mailout': "t",
            'mailout_failed': "t",
            'is_member': "t",
            "mailout_key": "sinister",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, new_name)
        self.assertEqual(member.email, 'snoo@whatver')
        self.assertEqual(member.address, "somewhere over the rainbow, I guess")
        self.assertEqual(member.posttown, "Town Town Town!")
        self.assertEqual(member.postcode, "< Sixteen chars?")
        self.assertEqual(member.country, "Suriname")
        self.assertEqual(member.website, "http://don't_care/")
        self.assertEqual(member.phone, "+44 0000000000000001")
        self.assertEqual(member.altphone, "-1 3202394 2352 23 234")
        self.assertEqual(member.notes, "plays the balalaika really badly")
        self.assertTrue(member.mailout)
        self.assertTrue(member.mailout_failed)
        self.assertTrue(member.is_member)

        # Shouldn't have been changed:
        self.assertEqual(member.mailout_key, member_mailout_key)

        self.assertContains(response, new_name)
        self.assertContains(response, "Member 02 updated")

    def test_edit_post_form_invalid_data_missing(self):
        member = Member.objects.get(pk=2)
        start_name = member.name

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'k': member.mailout_key,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        # Only mandatory field is "name":
        self.assertFormError(response, 'form', 'name', u'This field is required.')

        member = Member.objects.get(pk=2)
        self.assertEqual(start_name, member.name)

    def test_edit_post_form_no_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url)

        self._assert_redirect_to_login(response, url)

    def test_edit_post_form_incorrect_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'k': "the WRONG KEY",
        })
        self._assert_redirect_to_login(response, url)

    def test_edit_post_form_invalid_memberid(self):
        url = reverse("edit-member", kwargs={"member_id": 21212})
        response = self.client.post(url, data={
            'k': "the WRONG KEY",
        })
        # If the member doesn't exist then don't give a specific error to that
        # effect, just redirect to the login page:
        self._assert_redirect_to_login(response, url)


class TestEditMemberViewLoggedIn(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestEditMemberViewLoggedIn, self).setUp()
        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

    # GET tests ###########################################
    def test_edit_get_form(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

    def test_edit_get_form_invalid_memberid(self):
        url = reverse("edit-member", kwargs={"member_id": 21212})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # POST tests ###########################################
    # Only test differences from not logged in view...
    def test_edit_post_form_minimal_data(self):
        new_name = u'N\u018EW Name'

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, u"Tw\u020d Member")

        member_mailout_key = member.mailout_key

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={'name': new_name, }, follow=True)

        member = Member.objects.get(pk=2)
        # New name set:
        self.assertEqual(member.name, new_name)

        # Secret key shouldn't have been changed:
        self.assertEqual(member.mailout_key, member_mailout_key)

        # Should redirect to search page, with a success message inserted:
        self.assertRedirects(response, reverse("search-members"))
        self.assertContains(response, "Member 02 updated")

    def test_edit_post_form_invalid_data_missing(self):
        member = Member.objects.get(pk=2)
        start_name = member.name

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        # Only mandatory field is "name":
        self.assertFormError(response, 'form', 'name', u'This field is required.')

        member = Member.objects.get(pk=2)
        self.assertEqual(start_name, member.name)

    def test_edit_post_form_invalid_memberid(self):
        url = reverse("edit-member", kwargs={"member_id": 21212})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class TestUnsubscribeMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestUnsubscribeMemberView, self).setUp()

    def _assert_redirect_to_login(self, response, url, extra_parameters=""):
        expected_redirect = (
            reverse("login") +
            "?next=" +
            urllib.quote(url + extra_parameters)
        )
        self.assertRedirects(response, expected_redirect)

    def _assert_subscribed(self, member_id):
        member = Member.objects.get(pk=member_id)
        self.assertTrue(member.mailout)

    def _assert_unsubscribed(self, member_id):
        member = Member.objects.get(pk=member_id)
        self.assertFalse(member.mailout)

    # GET tests ###########################################
    def test_unsubscribe_get_form(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.get(url, data={
            'k': member.mailout_key,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")

        # Still subscribed:
        self._assert_subscribed(2)

    def test_unsubscribe_get_form_no_key(self):
        self._assert_subscribed(2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.get(url)

        self._assert_redirect_to_login(response, url)

        # Still subscribed:
        self._assert_subscribed(2)

    def test_unsubscribe_get_form_incorrect_key(self):
        self._assert_subscribed(2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.get(url, data={
            'k': "the WRONG KEY",
        })

        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

        self._assert_subscribed(2)

    def test_unsubscribe_get_form_invalid_memberid(self):
        url = reverse("unsubscribe-member", kwargs={"member_id": 21212})
        response = self.client.get(url, data={
            'k': "the WRONG KEY",
        })

        # If the member doesn't exist then don't give a specific error to that
        # effect, just redirect to the login page:
        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

    # POST tests ##########################################
    def test_unsubscribe_post_form(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'k': member.mailout_key,
            'action': 'unsubscribe',
            'confirm': 'yes',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")
        self.assertContains(response, u"Member 02 unsubscribed")

        # Not subscribed:
        self._assert_unsubscribed(2)

    def test_subscribe_post_form(self):
        member = Member.objects.get(pk=2)
        member.mailout = False
        member.save()

        self._assert_unsubscribed(2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'k': member.mailout_key,
            'action': 'subscribe',
            'confirm': 'yes',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")
        self.assertContains(response, u"Member 02 subscribed")

        # subscribed:
        self._assert_subscribed(2)

    def test_unsubscribe_post_form_no_confirm(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'k': member.mailout_key,
            'action': 'unsubscribe',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")
        self.assertNotContains(response, u"Member 02 unsubscribed")

        # Still subscribed:
        self._assert_subscribed(2)

    def test_unsubscribe_post_form_invalid_key(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'k': member.mailout_key + "x",
            'action': 'unsubscribe',
            'confirm': 'yes',
        })

        self._assert_redirect_to_login(response, url)

        # Still subscribed:
        self._assert_subscribed(2)

    # TODO: Should add further tests for when the user is logged in. But
    # it's not actually used, so don't bother...


class TestMemberMiscViews(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestMemberMiscViews, self).setUp()

        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

#    The SQL query used for the stats doesn't work with SQLite!
#    def test_get_stats(self):
#        url = reverse("member-statistics")
#        response = self.client.get(url)
#        self.assertTemplateUsed(response, "stats.html")

    def test_post_stats(self):
        url = reverse("member-statistics")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)

    def test_get_homepages(self):
        url = reverse("member-homepages")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "homepages.html")

        self.assertContains(response,
                            u'<a href="http://1.foo.test/" rel="nofollow">http://1.foo.test/</a>',
                            html=True)
        self.assertContains(response,
                            u'<a href="http://two.foo.test/" rel="nofollow">http://two.foo.test/</a>',
                            html=True)

    def test_post_homepages(self):
        url = reverse("member-homepages")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)


class TestActivateDeactivateVolunteer(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestActivateDeactivateVolunteer, self).setUp()
        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

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
        response = self.client.post(url, data={u"volunteer": u"2"}, follow=True)

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
        response = self.client.post(url, data={u"volunteer": u"4"}, follow=True)

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
        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))
        self.files_in_use = []

    def tearDown(self):
        for filename in self.files_in_use:
            try:
                if os.path.exists(filename):
                    os.unlink(filename)
            except OSError as ose:
                print "Couldn't delete file!", ose

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

        self.assertContains(response, "<title>Edit Volunteer Volunteer One</title>")
        self.assertContains(response,
                            '<a href="/tmp/path/to/portrait">',
                            html=False)

    def test_get_form_add(self):
        url = reverse("add-volunteer")
        response = self.client.get(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        self.assertContains(response, "<title>Add Volunteer</title>", html=True)
        # Should have default mugshot:
        self.assertContains(response,
                            '<img src="{0}" border="0" width="75">'.format(settings.DEFAULT_MUGSHOT),
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
        self.assertRedirects(response, reverse("view-volunteer-list"))

        self.assertContains(
            response,
            u'<li class="success">Created volunteer &#39;New Volunteer, called \u0187hri\u01a8topher&#39;</li>',
            html=True
        )

        # one more of each:
        self.assertEqual(Volunteer.objects.count(), init_vol_count + 1)
        self.assertEqual(Member.objects.count(), init_mem_count + 1)

        # New things:
        new_member = Member.objects.get(name=u"New Volunteer, called \u0187hri\u01a8topher")
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

        self.assertRedirects(response, reverse("view-volunteer-list"))

        self.assertContains(
            response,
            u'<li class="success">Created volunteer &#39;Another New Volunteer&#39;</li>',
            html=True
        )

        # one more of each:
        self.assertEqual(Volunteer.objects.count(), init_vol_count + 1)
        self.assertEqual(Member.objects.count(), init_mem_count + 1)

        # New things:
        new_member = Member.objects.get(name=u"Another New Volunteer")
        self.assertEqual(new_member.email, 'snoo@whatver.com')
        self.assertEqual(new_member.address, "somewhere over the rainbow, I guess")
        self.assertEqual(new_member.posttown, "Town Town Town!")
        self.assertEqual(new_member.postcode, "< Sixteen chars?")
        self.assertEqual(new_member.country, "Suriname")
        self.assertEqual(new_member.website, "http://still_don't_care/")
        self.assertEqual(new_member.phone, "+44 1000000000000001")
        self.assertEqual(new_member.altphone, "-1 3202394 2352 23 234")
        self.assertFalse(new_member.mailout)
        self.assertTrue(new_member.mailout_failed)
        self.assertTrue(new_member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(new_member.notes, None)

        self.assertTrue(new_member.volunteer.active)
        self.assertEqual(new_member.volunteer.notes, "plays the balalaika really badly")

        roles = new_member.volunteer.roles.all()

        self.assertEqual(len(roles), 2)
        self.assertEqual(roles[0].id, 2)
        self.assertEqual(roles[1].id, 3)

    def test_post_new_vol_invalid_missing_data(self):
        url = reverse("add-volunteer")
        response = self.client.post(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        # The only mandatory field (!)
        self.assertFormError(response, 'mem_form', 'name', u'This field is required.')

    def test_post_edit_vol_minimal_data(self):
        init_vol_count = Volunteer.objects.count()
        init_mem_count = Member.objects.count()

        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url, data={
            u'mem-name': u'Renam\u018fd Vol'
        }, follow=True)
        self.assertRedirects(response, reverse("view-volunteer-list"))

        self.assertContains(
            response,
            u'<li class="success">Updated volunteer &#39;Renam\u018fd Vol&#39;</li>',
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
        self.assertEqual(member.notes, None)

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

        self.assertRedirects(response, reverse("view-volunteer-list"))

        self.assertContains(
            response,
            u'<li class="success">Updated volunteer &#39;Renam\u018fd Vol&#39;</li>',
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
        self.assertTrue(member.mailout_failed)
        self.assertTrue(member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(member.notes, None)

        self.assertTrue(member.volunteer.active)
        self.assertEqual(member.volunteer.notes, "plays the balalaika really badly")

        roles = member.volunteer.roles.all()

        self.assertEqual(len(roles), 2)
        self.assertEqual(roles[0].id, 2)
        self.assertEqual(roles[1].id, 3)

    def test_post_update_vol_invalid_missing_data(self):
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
        response = self.client.post(url)

        self.assertTemplateUsed(response, "form_volunteer.html")

        # The only mandatory field (!)
        self.assertFormError(response, 'mem_form', 'name', u'This field is required.')

    def test_post_update_vol_invalid_vol_id(self):
        url = reverse("edit-volunteer", kwargs={"volunteer_id": 10001})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_update_vol_clear_portrait(self):

        temp_jpg = tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-", suffix=".jpg", delete=False)

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
        self.assertRedirects(response, reverse("view-volunteer-list"))

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(vol.member.name, u'Pictureless Person')
        self.assertEqual(vol.portrait, '')

        # Should have deleted the old images:
        self.assertFalse(os.path.isfile(temp_jpg.name))

    @override_settings(MEDIA_ROOT="/tmp")
    def test_post_update_vol_change_portrait_success(self):
        temp_old_jpg = tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-", suffix=".jpg", delete=False)

        expected_upload_path = os.path.join('/tmp', settings.VOLUNTEER_PORTRAIT_DIR, "image_bluesq.jpg")

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
        new_jpg_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data", "image_bluesq.jpg")

        with open(new_jpg_filename, "rb") as new_jpg_file:
            # Post an edit to update the image:
            url = reverse("edit-volunteer", kwargs={"volunteer_id": 1})
            response = self.client.post(url, data={
                u'mem-name': u'Pictureless Person',
                u'vol-portrait': new_jpg_file,
            })

        self.assertRedirects(response, reverse("view-volunteer-list"))

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(vol.member.name, u'Pictureless Person')

        # Portrait path should be:
        self.assertEqual(vol.portrait.name, os.path.join(settings.VOLUNTEER_PORTRAIT_DIR, "image_bluesq.jpg"))
        # And should have 'uploaded' file to:
        self.assertTrue(os.path.isfile(expected_upload_path))

        # Should have deleted the old images:
        self.assertFalse(os.path.isfile(temp_old_jpg.name))

        # XXX do this properly:
        shutil.rmtree(os.path.join('/tmp', settings.VOLUNTEER_PORTRAIT_DIR))


class TestMemberMailoutTask(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestMemberMailoutTask, self).setUp()
        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def _assert_mail_as_expected(self, msgstr, is_utf8, from_addr, dest_addr, body_contains, expected_subject):
        message = email.parser.Parser().parsestr(msgstr)

        self.assertEqual(message.get_content_type(), 'text/plain')
        self.assertFalse(message.is_multipart())
        if is_utf8:
            self.assertEqual(message.get_charsets(), ["utf-8"])
            self.assertEqual(message['Content-Transfer-Encoding'], '8bit')
        else:
            self.assertEqual(message.get_charsets(), ["us-ascii"])
            self.assertEqual(message['Content-Transfer-Encoding'], '7bit')
        self.assertEqual(message['From'], from_addr)
        self.assertEqual(message['To'], dest_addr)

        body = message.get_payload().decode("utf-8")
        subject = email.header.decode_header(message['Subject'])

        self.assertIn(body_contains, body)
        subject = subject[0][0].decode(subject[0][1]) if subject[0][1] else subject[0][0]
        self.assertEqual(subject, expected_subject)

    def _assert_mail_sent(self, result, current_task_mock, smtplib_mock, subject, body, is_utf8):
        current_task_mock.update_state.assert_has_calls([
            call(state='PROGRESS017', meta={'total': 6, 'sent': 1}),
            call(state='PROGRESS034', meta={'total': 6, 'sent': 2}),
            call(state='PROGRESS051', meta={'total': 6, 'sent': 3}),
            call(state='PROGRESS067', meta={'total': 6, 'sent': 4}),
            call(state='PROGRESS084', meta={'total': 6, 'sent': 5}),
            # 101% complete! (ahem)
            call(state='PROGRESS101', meta={'total': 6, 'sent': 6})
        ])

        # Expect to have connected:
        smtplib_mock.assert_called_once_with('smtp.test', 8281)

        # Sent 6 mails, plus one summary:
        conn = smtplib_mock.return_value
        self.assertEqual(conn.sendmail.call_count, 7)

        # Validate summary:
        summary_mail_call = conn.sendmail.call_args_list[6]
        self.assertEqual(summary_mail_call[0][0], settings.MAILOUT_FROM_ADDRESS)
        self.assertEqual(summary_mail_call[0][1], [settings.MAILOUT_DELIVERY_REPORT_TO])
        self._assert_mail_as_expected(
            summary_mail_call[0][2],
            is_utf8,
            settings.MAILOUT_FROM_ADDRESS,
            settings.MAILOUT_DELIVERY_REPORT_TO,
            u"6 copies of the following were sent out on cube members list",
            subject
        )

        # Reported success:
        # False => no error, 6 == sent count:
        self.assertEqual(result, (False, 6, 'Ok'))

        # Disconnect:
        conn.quite.assert_called_once()

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_unicode(self, current_task_mock, smtplib_mock):
        subject = u"The Subject \u2603!"
        body = u"The Body!\nThat will be \u20ac1, please\nTa \u2603!"
        result = toolkit.members.tasks.send_mailout(subject, body)
        self._assert_mail_sent(result, current_task_mock, smtplib_mock, subject, body, True)

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_ascii(self, current_task_mock, smtplib_mock):
        subject = u"The Subject!"
        body = u"The Body!\nThat will be $1, please\nTa!"
        result = toolkit.members.tasks.send_mailout(subject, body)
        self._assert_mail_sent(result, current_task_mock, smtplib_mock, subject, body, False)

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_iso88591_subj(self, current_task_mock, smtplib_mock):
        subject = u"The \xa31 Subject!"
        body = u"The Body!\nThat will be $1, please\nTa!"
        result = toolkit.members.tasks.send_mailout(subject, body)
        self._assert_mail_sent(result, current_task_mock, smtplib_mock, subject, body, False)

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_connect_fail(self, current_task_mock, smtplib_mock):
        smtplib_mock.side_effect = smtplib.SMTPConnectError("Blah", 101)

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        self.assertEqual(result, (True, 0, "Failed to connect to SMTP server: ('Blah', 101)"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_fail(self, current_task_mock, smtplib_mock):
        smtplib_mock.return_value.sendmail.side_effect = smtplib.SMTPException("Something failed", 101)

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        # Overall, operation succeeded:
        self.assertEqual(result, (False, 6, "Ok"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_send_fail_disconnected(self, current_task_mock, smtplib_mock):
        smtplib_mock.return_value.sendmail.side_effect = smtplib.SMTPServerDisconnected("Something failed", 101)

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        self.assertEqual(result, (True, 0, "Mailout job died: ('Something failed', 101)"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_random_error(self, current_task_mock, smtplib_mock):
        # Test a non SMTP error
        smtplib_mock.return_value.sendmail.side_effect = IOError("something")

        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        # Overall, operation succeeded:
        self.assertEqual(result, (True, 0, "Mailout job died: something"))

    @patch("smtplib.SMTP")
    @patch("toolkit.members.tasks.current_task")
    @override_settings(EMAIL_HOST="smtp.test", EMAIL_PORT=8281)
    def test_no_recipients(self, current_task_mock, smtplib_mock):
        Member.objects.all().delete()
        # Test a non SMTP error
        result = toolkit.members.tasks.send_mailout(
            u"The \xa31 Subject!", u"The Body!\nThat will be $1, please\nTa!"
        )

        self.assertEqual(result, (True, 0, "No recipients found"))
