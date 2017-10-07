from __future__ import print_function
import shutil
import os.path
import tempfile
import binascii

from mock import patch

from six.moves import urllib
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.conf import settings

import django.contrib.auth.models as auth_models

from toolkit.members.models import Member, Volunteer
import toolkit.members.member_views as member_views

from .common import MembersTestsMixin

TINY_VALID_BASE64_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAAXNSR0IArs4c6QAAAARnQU1BA"
    "ACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAMSURBVBhXY/j//z8ABf4C/qc1gYQAAA"
    "AASUVORK5CYII=")


class SecurityTests(MembersTestsMixin, TestCase):

    """Basic test that the private pages do not load without a login"""

    write_required = {
        # Volunteer urls:
        'add-volunteer': {},
        'edit-volunteer': {'volunteer_id': 1},
        'activate-volunteer': {},
        'inactivate-volunteer': {},
        # Member urls:
        'add-member': {},
        'edit-member': {'member_id': 1},
        'delete-member': {'member_id': 1},
    }

    only_read_required = {
        # Volunteer urls:
        'view-volunteer-list': {},
        'view-volunteer-role-report': {},
        'unretire-select-volunteer': {},
        'retire-select-volunteer': {},
        # Member urls:
        'search-members': {},
        'view-member': {'member_id': 1},
        'member-statistics': {},
    }

    def _assert_need_login(self, views_to_test):
        """Assert that given URLs 302 redirect to the login page"""
        for view_name, kwargs in views_to_test.items():
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

        self._assert_need_login(views_to_test)

    def test_need_write(self):
        """
        Checks all URLs that shouldn't work when logged in user doesn't have
        'toolkit.write' permission
        """
        # login as read only user:
        self.client.login(username="read_only", password="T3stPassword!1")
        self._assert_need_login(self.write_required)

    def test_need_read_or_write(self):
        """
        Checks all URLs that shouldn't work when logged in user doesn't have
        'toolkit.write' or 'toolkit.read' permission
        """
        views_to_test = {}
        views_to_test.update(self.write_required)
        views_to_test.update(self.only_read_required)

        # login as no permission user:
        self.client.login(username="no_perm", password="T3stPassword!2")

        self._assert_need_login(views_to_test)

    def test_protected_urls(self):
        """URLs which should only work if the member key is known"""

        views_to_test = (
            'edit-member',
            'unsubscribe-member',
        )

        member = Member.objects.get(id=1)

        # First try without a key:
        for view_name in views_to_test:
            url = reverse(view_name, kwargs={'member_id': member.id})
            expected_redirect = "{0}?next={1}".format(
                reverse("login"), url)

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


class AddMemberIPAuth(TestCase):

    def setUp(self):
        factory = RequestFactory()
        self.url = reverse("add-member")
        self.request = factory.get(self.url)
        self.request.user = auth_models.AnonymousUser()

    def test_auth_by_ip_matching_ip_denied(self):
        # Request should be denied from 127.0.0.1

        # Check that this shouldn't work
        self.assertNotIn('127.0.0.1', settings.CUBE_IP_ADDRESSES)

        # Issue the request
        response = member_views.add_member(self.request)

        expected_redirect = (
            "{0}?next={1}"
            .format(reverse("login"), self.url)
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], expected_redirect)

    def test_auth_by_ip_matching_ip_permitted(self):
        # Request should be permitted from IP in settings

        # Check that this should work:
        self.assertTrue(len(settings.CUBE_IP_ADDRESSES))

        # set source IP:
        self.request.META['REMOTE_ADDR'] = settings.CUBE_IP_ADDRESSES[0]

        # Issue the request
        response = member_views.add_member(self.request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Location', response)


class TestMemberModelManager(MembersTestsMixin, TestCase):

    def test_email_recipients(self):
        recipients = Member.objects.mailout_recipients()
        self.assertEqual(recipients.count(), 6)
        for member in recipients:
            self.assertTrue(member.mailout)
            self.assertFalse(member.mailout_failed)
            self.assertTrue(member.email)


class TestMemberModel(TestCase):

    def setUp(self):
        member_one = Member(name="Member One", number="1",
                            email="one@example.com")
        member_one.save()

    def test_membership_number_no_existing(self):
        new_member = Member(name="Member two", email="two@example.com")
        new_member.save()
        self.assertEqual(str(new_member.pk), new_member.number)

    def test_membership_number_exists(self):
        old_member = Member.objects.get(id=1)
        old_member.number = "2"
        old_member.save()

        new_member = Member(name="Member two", email="two@example.com")
        new_member.save()
        self.assertEqual("100002", new_member.number)

    def test_membership_number_exists_twice(self):
        old_member = Member.objects.get(id=1)
        old_member.number = "3"
        old_member.save()

        new_member_one = Member(name="Member two", email="two@example.com")
        new_member_one.save()
        new_member_one.number = "100003"
        new_member_one.save()

        new_member_two = Member(name="Member two", email="two@example.com")
        new_member_two.save()
        self.assertEqual("200003", new_member_two.number)

    def test_membership_number_custom(self):
        new_member = Member(name="Member two", email="two@example.com")
        new_member.number = "Orange squash"
        new_member.save()

        new_member = Member.objects.get(id=new_member.pk)
        self.assertEqual(new_member.number, "Orange squash")

    def test_membership_number_custom_edit(self):
        old_member = Member.objects.get(id=1)
        old_member.number = "Orange squash"
        old_member.save()

        old_member = Member.objects.get(id=1)
        self.assertEqual(old_member.number, "Orange squash")


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


class TestAddMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestAddMemberView, self).setUp()

        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

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
            u"mailout": "on",
        }, follow=True)

        self.assertRedirects(response, url)
        self.assertTemplateUsed(response, "form_new_member.html")

        member = Member.objects.get(name=new_name)
        self.assertEqual(
            member.email, u"blah.blah-blah@hard-to-tell-if-genuine.uk")
        self.assertEqual(member.postcode, u"SW1A 1AA")
        self.assertEqual(member.mailout, True)

        self.assertContains(
            response, u"Added member: {0}".format(member.number))

    def test_post_minimal_submission(self):
        new_name = u"Another New \u20acejit"

        self.assertEqual(Member.objects.filter(name=new_name).count(), 0)

        url = reverse("add-member")
        response = self.client.post(url, data={
            u"name": new_name,
        }, follow=True)

        self.assertRedirects(response, url)
        self.assertTemplateUsed(response, "form_new_member.html")

        member = Member.objects.get(name=new_name)
        self.assertEqual(member.email, u"")
        self.assertEqual(member.postcode, u"")
        self.assertEqual(member.is_member, False)

        self.assertContains(
            response, u"Added member: {0}".format(member.number))

    def test_post_form_invalid_data_missing(self):
        url = reverse("add-member")
        response = self.client.post(url)

        count_before = Member.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_member.html")

        self.assertFormError(response, 'form', 'name',
                             u'This field is required.')

        self.assertEqual(count_before, Member.objects.count())

    def test_invalid_method(self):
        url = reverse("add-member")
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)


class TestSearchMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestSearchMemberView, self).setUp()

        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

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

        self.assertContains(
            response, u"<td><a href='/members/1'>Member On\u0205</a></td>",
            html=True)
        self.assertContains(
            response, u'<a href="mailto:one@example.com">one@example.com</a>',
            html=True)
        self.assertContains(response, u"<td>BS1 1AA</td>", html=True)

        self.assertContains(
            response, u"<td><a href='/members/2'>Tw\u020d Member</a></td>",
            html=True)
        self.assertContains(
            response, u'<a href="mailto:two@example.com">two@example.com</a>',
            html=True)

        self.assertContains(
            response, u"<td><a href='/members/3'>Some Third Chap</a></td>",
            html=True)
        self.assertContains(
            response,
            u'<td><a href="mailto:two@member.test">two@member.test</a></td>',
            html=True)
        self.assertContains(response, u"<td>NORAD</td>", html=True)

        # Should have Edit / Delete buttons:
        self.assertContains(
            response, u'<input type="submit" value="Edit">', html=True)
        self.assertContains(
            response, u'<input type="submit" value="Delete">', html=True)

        expected_edit_form = ('<form method="get" action="{0}">'
                              '<input type="submit" value="Edit"></form>'
                              .format(reverse(
                                  "edit-member", kwargs={"member_id": 3})))

        expected_delete_form = ('<form class="delete" method="post" '
                                'action="{0}">'
                                .format(reverse(
                                    "delete-member", kwargs={"member_id": 3})))
        self.assertContains(response, expected_edit_form)
        self.assertContains(response, expected_delete_form)

    def test_query_no_results(self):
        url = reverse("search-members")

        response = self.client.get(url, data={'q': u'toast'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")


class TestDeleteMemberView(MembersTestsMixin, TestCase):

    def setUp(self):
        super(TestDeleteMemberView, self).setUp()

        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

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
            urllib.parse.quote(url + extra_parameters)
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
            'email': 'snoo@whatver.com',
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
        self.assertEqual(member.email, 'snoo@whatver.com')
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

    def test_edit_post_form_invalid_emails(self):
        new_name = u'N\u018EW Name'

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, u"Tw\u020d Member")
        member_mailout_key = member.mailout_key
        self.assertTrue(member.is_member)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url, data={
            'name': new_name,
            'email': 'definitely_invalid@example/com',
            'k': member_mailout_key,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        self.assertFormError(response, 'form', 'email',
                             u'Enter a valid email address.')

        member = Member.objects.get(pk=2)
        self.assertNotEqual(member.name, new_name)
        self.assertEqual(member.email, "two@example.com")
        self.assertEqual(member.mailout_key, member_mailout_key)

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
        self.assertFormError(response, 'form', 'name',
                             u'This field is required.')

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
        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

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
        response = self.client.post(
            url, data={'name': new_name, }, follow=True)

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
        self.assertFormError(response, 'form', 'name',
                             u'This field is required.')

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
            urllib.parse.quote(url + extra_parameters)
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

        self.assertTrue(self.client.login(
            username="admin", password="T3stPassword!"))

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

        self.assertContains(
            response,
            u'<a href="http://1.foo.test/" '
            u'rel="nofollow">http://1.foo.test/</a>',
            html=True)
        self.assertContains(
            response,
            u'<a href="http://two.foo.test/" '
            u'rel="nofollow">http://two.foo.test/</a>',
            html=True)

    def test_post_homepages(self):
        url = reverse("member-homepages")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)


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
            '<img id="photo" alt="No photo yet" '
            'src="{0}" border="0" width="75">'
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
        self.assertRedirects(response, reverse("view-volunteer-list"))

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

        self.assertRedirects(response, reverse("view-volunteer-list"))

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
        self.assertTrue(new_member.mailout_failed)
        self.assertTrue(new_member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(new_member.notes, None)

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
        self.assertRedirects(response, reverse("view-volunteer-list"))

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
        self.assertTrue(member.mailout_failed)
        self.assertTrue(member.is_member)
        # Member notes aren't included on the form:
        self.assertEqual(member.notes, None)

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
        self.assertRedirects(response, reverse("view-volunteer-list"))

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

        self.assertRedirects(response, reverse("view-volunteer-list"))

        vol = Volunteer.objects.get(id=1)
        self.assertEqual(vol.member.name, u'Pictureless Person')

        # Portrait path should be:
        self.assertEqual(vol.portrait.name, os.path.join(
            settings.VOLUNTEER_PORTRAIT_DIR, "image_bluesq.jpg"))
        # And should have 'uploaded' file to:
        self.assertTrue(os.path.isfile(expected_upload_path))

        # Should have deleted the old images:
        self.assertFalse(os.path.isfile(temp_old_jpg.name))

        # XXX do this properly:
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

        self.assertRedirects(response, reverse("view-volunteer-list"))

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

        # XXX do this properly!
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
