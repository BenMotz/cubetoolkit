from __future__ import print_function
from mock import patch

from six.moves import urllib
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.conf import settings

import django.contrib.auth.models as auth_models

from toolkit.members.models import Member
import toolkit.members.member_views as member_views

from .common import MembersTestsMixin


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
