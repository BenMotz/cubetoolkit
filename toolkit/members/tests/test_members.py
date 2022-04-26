import datetime

from mock import patch
import urllib

from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.conf import settings
from django.test.utils import override_settings

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
        self.assertNotIn("127.0.0.1", settings.CUBE_IP_ADDRESSES)

        # Issue the request
        response = member_views.add_member(self.request)

        expected_redirect = "{0}?next={1}".format(reverse("login"), self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], expected_redirect)

    def test_auth_by_ip_matching_ip_permitted(self):
        # Request should be permitted from IP in settings

        # Check that this should work:
        self.assertTrue(len(settings.CUBE_IP_ADDRESSES))

        # set source IP:
        self.request.META["REMOTE_ADDR"] = settings.CUBE_IP_ADDRESSES[0]

        # Issue the request
        response = member_views.add_member(self.request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response)


@patch("toolkit.members.models.timezone_now")
class TestMemberModelManagerBase(MembersTestsMixin):
    def test_email_recipients(self, now_mock):
        recipients = Member.objects.mailout_recipients()
        self.assertEqual(recipients.count(), 6)
        for member in recipients:
            self.assertTrue(member.mailout)
            self.assertFalse(member.mailout_failed)
            self.assertTrue(member.email)

    def test_expired(self, now_mock):
        now_mock.return_value.date.return_value = datetime.date(
            day=1, month=6, year=2010
        )

        members = Member.objects.expired().all()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0], self.mem_2)

    def test_unexpired(self, now_mock):
        now_mock.return_value.date.return_value = datetime.date(
            day=1, month=6, year=2010
        )

        members = Member.objects.unexpired().all()
        self.assertEqual(len(members), 8)


@override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
class TestMemberModelManagerExpiryEnabled(
    TestMemberModelManagerBase, TestCase
):
    pass


@override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
class TestMemberModelManagerExpiryDisabled(
    TestMemberModelManagerBase, TestCase
):
    pass


class TestMemberModel(TestCase):
    def setUp(self):
        member_one = Member(
            name="Member One", number="1", email="one@example.com"
        )
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

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    @override_settings(MEMBERSHIP_LENGTH_DAYS=100)
    @patch("toolkit.members.models.timezone_now")
    def test_default_expiry_expiry_enabled(self, now_mock):
        now_mock.return_value.date.return_value = datetime.date(
            day=1, month=1, year=2000
        )

        new_member = Member(name="New Member")
        new_member.save()

        new_member.refresh_from_db()
        self.assertEqual(
            new_member.membership_expires, datetime.date(2000, 4, 10)
        )
        self.assertFalse(new_member.has_expired())

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
    def test_default_expiry_expiry_disabled(self):
        new_member = Member(name="New Member")
        new_member.save()

        new_member.refresh_from_db()
        self.assertIsNone(new_member.membership_expires)
        self.assertFalse(new_member.has_expired())


class TestAddMemberView(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestAddMemberView, self).setUp()

        self.assertTrue(
            self.client.login(username="admin", password="T3stPassword!")
        )

    def tearDown(self):
        self.client.logout()

    def test_get_form(self):
        url = reverse("add-member")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_member.html")

    def _test_post_form_common(self, now_mock, expiry_enabled):
        now_mock.return_value.date.return_value = datetime.date(
            day=1, month=1, year=2000
        )

        new_name = "Some New \u20acejit"

        self.assertEqual(Member.objects.filter(name=new_name).count(), 0)

        url = reverse("add-member")
        response = self.client.post(
            url,
            data={
                "name": new_name,
                "email": "blah.blah-blah@hard-to-tell-if-genuine.uk",
                "postcode": "SW1A 1AA",
                "mailout": "on",
            },
            follow=True,
        )

        self.assertRedirects(response, url)
        self.assertTemplateUsed(response, "form_new_member.html")

        member = Member.objects.get(name=new_name)
        self.assertEqual(
            member.email, "blah.blah-blah@hard-to-tell-if-genuine.uk"
        )
        self.assertEqual(member.postcode, "SW1A 1AA")
        self.assertEqual(member.mailout, True)
        if expiry_enabled:
            self.assertEqual(
                member.membership_expires, datetime.date(2000, 4, 11)
            )
        else:
            self.assertIsNone(member.membership_expires)

        self.assertContains(
            response, "Added member: {0}".format(member.number)
        )

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
    @patch("toolkit.members.models.timezone_now")
    def test_post_form_expiry_disabled(self, now_mock):
        self._test_post_form_common(now_mock, expiry_enabled=False)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    @override_settings(MEMBERSHIP_LENGTH_DAYS=101)
    @patch("toolkit.members.models.timezone_now")
    def test_post_form_expiry_enabled(self, now_mock):
        self._test_post_form_common(now_mock, expiry_enabled=True)

    def test_post_minimal_submission(self):
        new_name = "Another New \u20acejit"

        self.assertEqual(Member.objects.filter(name=new_name).count(), 0)

        url = reverse("add-member")
        response = self.client.post(
            url,
            data={
                "name": new_name,
            },
            follow=True,
        )

        self.assertRedirects(response, url)
        self.assertTemplateUsed(response, "form_new_member.html")

        member = Member.objects.get(name=new_name)
        self.assertEqual(member.email, "")
        self.assertEqual(member.postcode, "")
        self.assertEqual(member.is_member, False)

        self.assertContains(
            response, "Added member: {0}".format(member.number)
        )

    def test_post_form_invalid_data_missing(self):
        count_before = Member.objects.count()

        url = reverse("add-member")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_member.html")

        self.assertFormError(
            response, "form", "name", "This field is required."
        )

        self.assertEqual(count_before, Member.objects.count())

    def test_post_form_invalid_duplicate_email(self):

        count_before = Member.objects.count()

        url = reverse("add-member")
        response = self.client.post(
            url,
            data={
                "name": "another new member",
                "email": self.mem_1.email,
                "mailout": "on",
            },
            follow=True,
        )

        # Should have redirected to the search form, with the email address as
        # the search term:
        expected_url = reverse("search-members")
        self.assertRedirects(
            response, expected_url + "?email=%s&q=" % self.mem_1.email
        )

        self.assertTemplateUsed(response, "search_members_results.html")
        # A new shouldn't have been created
        self.assertEqual(count_before, Member.objects.count())

    def test_invalid_method(self):
        url = reverse("add-member")
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)


class TestSearchMemberView(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestSearchMemberView, self).setUp()

        self.assertTrue(
            self.client.login(username="admin", password="T3stPassword!")
        )

    def tearDown(self):
        self.client.logout()

    @patch("toolkit.members.member_views.Member")
    def test_no_query(self, member_patch):
        url = reverse("search-members")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members.html")

        self.assertFalse(member_patch.objects.filter.called)

    def _common_test_query_with_results(self, now_mock, expiry_enabled):
        now_mock.return_value.date.return_value = datetime.date(
            day=1, month=6, year=2010
        )

        url = reverse("search-members")
        response = self.client.get(url, data={"q": "member"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")

        self.assertContains(
            response,
            "<td><a href='/members/1'>Member On\u0205</a></td>",
            html=True,
        )
        self.assertContains(
            response,
            '<a href="mailto:one@example.com">one@example.com</a>',
            html=True,
        )
        self.assertContains(response, "<td>BS1 1AA</td>", html=True)

        self.assertContains(
            response,
            "<td><a href='/members/2'>Tw\u020d Member</a></td>",
            html=True,
        )
        self.assertContains(
            response,
            '<a href="mailto:two@example.com">two@example.com</a>',
            html=True,
        )

        self.assertContains(
            response,
            "<td><a href='/members/3'>Some Third Chap</a></td>",
            html=True,
        )
        self.assertContains(
            response,
            '<td><a href="mailto:two@member.test">two@member.test</a></td>',
            html=True,
        )
        self.assertContains(response, "<td>NORAD</td>", html=True)

        if expiry_enabled:
            self.assertContains(
                response, "<th>Membership expires</th>", html=True
            )
            self.assertContains(
                response, '<td class="expired">31/05/2010</td>', html=True
            )
            self.assertContains(response, "<td>01/06/2010</td>", html=True)
            self.assertContains(response, "expires")
        else:
            self.assertNotContains(response, "expires")

        # Should have Edit / Delete buttons:
        self.assertContains(
            response, '<input type="submit" value="Edit">', html=True
        )
        self.assertContains(
            response, '<input type="submit" value="Delete">', html=True
        )

        expected_edit_form = (
            '<form method="get" action="{0}">'
            '<input type="submit" value="Edit"></form>'.format(
                reverse("edit-member", kwargs={"member_id": 3})
            )
        )

        expected_delete_form = (
            '<form class="delete" method="post" '
            'action="{0}">'.format(
                reverse("delete-member", kwargs={"member_id": 3})
            )
        )
        self.assertContains(response, expected_edit_form)
        self.assertContains(response, expected_delete_form)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
    @patch("toolkit.members.models.timezone_now")
    def test_query_with_results_expiry_disabled(self, now_mock):
        self._common_test_query_with_results(now_mock, expiry_enabled=False)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    @patch("toolkit.members.models.timezone_now")
    def test_query_with_results_expiry_enabled(self, now_mock):
        self._common_test_query_with_results(now_mock, expiry_enabled=True)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
    @patch("toolkit.members.models.timezone_now")
    def test_email_query_with_results_expiry_disabled(self, now_mock):
        url = reverse("search-members")
        response = self.client.get(url, data={"email": self.mem_2.email})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")

        self.assertContains(
            response,
            "<td><a href='/members/2'>Tw\u020d Member</a></td>",
            html=True,
        )
        self.assertContains(
            response,
            '<a href="mailto:two@example.com">two@example.com</a>',
            html=True,
        )

        self.assertNotContains(response, "expires")

    def test_query_no_results(self):
        url = reverse("search-members")

        testcases = [
            ("q", {"q": "toast"}),
            ("email", {"email": "toast@infinite.monkey"}),
            ("both", {"q": "tost", "email": "toast@infinite.monkey"}),
        ]
        for name, testcase in testcases:
            with self.subTest(name):
                response = self.client.get(url, data=testcase)

                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(
                    response, "search_members_results.html"
                )

    def test_email_query_no_results(self):
        url = reverse("search-members")

        response = self.client.get(url, data={"email": "toast@infinity.com"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_members_results.html")


class TestDeleteMemberViewLoggedIn(MembersTestsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(
            self.client.login(username="admin", password="T3stPassword!")
        )

    def tearDown(self):
        self.client.logout()

    def test_delete_non_volunteer(self):
        self.assertEqual(Member.objects.filter(id=1).count(), 1)

        url = reverse("delete-member", kwargs={"member_id": 1})
        response = self.client.post(url, follow=True)

        self.assertRedirects(response, reverse("search-members"))
        self.assertContains(response, "Deleted member: 1 (Member On\u0205)")

        self.assertEqual(Member.objects.filter(id=1).count(), 0)

    def test_delete_volunteer(self):
        mem = self.vol_1.member
        self.assertTrue(Member.objects.filter(id=mem.id).exists())

        url = reverse("delete-member", kwargs={"member_id": mem.id})
        response = self.client.post(url, follow=True)

        self.assertRedirects(response, reverse("search-members"))
        self.assertContains(
            response, "Can&#39;t delete active volunteer %s" % mem.name
        )

        self.assertTrue(Member.objects.filter(id=mem.id).exists())

    def test_delete_nonexistent(self):
        url = reverse("delete-member", kwargs={"member_id": 1000})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_get_form_no_key_logged_in(self):
        self.assertEqual(Member.objects.filter(id=1).count(), 1)

        url = reverse("delete-member", kwargs={"member_id": 1})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Member.objects.filter(id=1).count(), 1)


class TestDeleteMemberViewNotLoggedIn(MembersTestsMixin, TestCase):
    def _assert_redirect_to_login(self, response, url, extra_parameters=""):
        expected_redirect = (
            reverse("login")
            + "?next="
            + urllib.parse.quote(url + extra_parameters)
        )
        self.assertRedirects(response, expected_redirect)

    def setUp(self):
        super().setUp()
        self.assertEqual(Member.objects.filter(id=self.mem_1.id).count(), 1)

    def tearDown(self):
        super().tearDown()

    def test_delete_get_form_no_key(self):

        url = reverse("delete-member", kwargs={"member_id": 1})

        response = self.client.get(url)

        self._assert_redirect_to_login(response, url)
        self.assertEqual(Member.objects.filter(id=1).count(), 1)

    def test_delete_get_form_wrong_key(self):
        url = reverse("delete-member", kwargs={"member_id": 1})

        response = self.client.get(url, data={"k": "badkey"})

        self._assert_redirect_to_login(response, url, "?k=badkey")
        self.assertEqual(Member.objects.filter(id=self.mem_1.id).count(), 1)

    def test_delete_get_form_valid_key_no_confirmation(self):
        url = reverse("delete-member", kwargs={"member_id": self.mem_1.id})

        for confirmed in ["no", "nope", "", None, "1", "0", "yeees", "Yes"]:
            data = {"k": self.mem_1.mailout_key}
            with self.subTest(confirmed_string=confirmed):
                if confirmed is not None:
                    data["confirmed"] = confirmed
                response = self.client.get(url, data=data)
                # Shouldn't have been deleted yet:
                self.assertEqual(
                    Member.objects.filter(id=self.mem_1.id).count(), 1
                )

                # Should have used the "pls confirm" form:
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "confirm-deletion.html")

    def test_delete_get_form_valid_key_confirm(self):
        url = reverse("delete-member", kwargs={"member_id": self.mem_1.id})

        response = self.client.get(
            url,
            data={
                "k": self.mem_1.mailout_key,
                "confirmed": "yes",
            },
        )

        # Should have been deleted:
        self.assertEqual(Member.objects.filter(id=self.mem_1.id).count(), 0)
        self.assertRedirects(response, reverse("goodbye"))

    def test_delete_active_volunteer_fails(self):
        mem = self.vol_1.member
        self.assertTrue(Member.objects.filter(id=mem.id).exists())

        url = reverse("delete-member", kwargs={"member_id": mem.id})

        response = self.client.get(
            url,
            data={
                "k": mem.mailout_key,
                # confirmed shouldn't make a difference, but belt+braces:
                "confirmed": "yes",
            },
        )

        # Should not have been deleted:
        self.assertTrue(Member.objects.filter(id=mem.id).exists())
        # Should have been politely told to email the admins:
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "email_admin.html")

    def test_delete_inactive_volunteer_succeeds(self):
        mem = self.vol_1.member
        self.assertTrue(Member.objects.filter(id=mem.id).exists())

        # Retire:
        self.vol_1.active = False
        self.vol_1.save()

        url = reverse("delete-member", kwargs={"member_id": mem.id})
        response = self.client.get(
            url,
            data={
                "k": mem.mailout_key,
                "confirmed": "yes",
            },
        )

        # Should have been deleted:
        self.assertEqual(Member.objects.filter(id=mem.id).count(), 0)
        self.assertRedirects(response, reverse("goodbye"))


class TestEditMemberViewNotLoggedIn(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestEditMemberViewNotLoggedIn, self).setUp()

    def _assert_redirect_to_login(self, response, url, extra_parameters=""):
        expected_redirect = (
            reverse("login")
            + "?next="
            + urllib.parse.quote(url + extra_parameters)
        )
        self.assertRedirects(response, expected_redirect)

    # GET tests ###########################################
    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    def test_edit_get_form(self):
        member = Member.objects.get(pk=2)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(
            url,
            data={
                "k": member.mailout_key,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        # Shouldn't have these fields
        self.assertNotContains(response, "expires:")
        self.assertNotContains(response, "Is member")

    def test_edit_get_form_no_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(url)

        self._assert_redirect_to_login(response, url)

    def test_edit_get_form_incorrect_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.get(
            url,
            data={
                "k": "the WRONG KEY",
            },
        )
        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

    def test_edit_get_form_invalid_memberid(self):
        url = reverse("edit-member", kwargs={"member_id": 21212})
        response = self.client.get(
            url,
            data={
                "k": "the WRONG KEY",
            },
        )
        # If the member doesn't exist then don't give a specific error to that
        # effect, just redirect to the login page:
        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

    # POST tests ###########################################
    def test_edit_post_form_minimal_data(self):
        new_name = "N\u018EW Name"

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, "Tw\u020d Member")
        member_mailout_key = member.mailout_key
        self.assertTrue(member.is_member)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "name": new_name,
                "k": member_mailout_key,
            },
        )
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
        # Shouldn't have been changed:
        self.assertTrue(member.is_member)

        # Shouldn't have been changed:
        self.assertEqual(member.mailout_key, member_mailout_key)

        self.assertContains(response, new_name)
        self.assertContains(response, "Member 02 updated")

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    def test_edit_post_form_all_data(self):
        new_name = "N\u018EW Name"

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, "Tw\u020d Member")
        member_mailout_key = member.mailout_key
        self.assertTrue(member.is_member)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "name": new_name,
                "email": "snoo@whatver.com",
                "k": member_mailout_key,
                "address": "somewhere over the rainbow, I guess",
                "posttown": "Town Town Town!",
                "postcode": "< Sixteen chars?",
                "country": "Suriname",
                "website": "http://don't_care/",
                "phone": "+44 0000000000000001",
                "altphone": "-1 3202394 2352 23 234",
                "notes": "plays the balalaika really badly",
                "mailout": "t",
                "mailout_failed": "t",
                "is_member": "t",
                # Should be ignored:
                "mailout_key": "sinister",
                "membership_expires": "01/01/2020",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, new_name)
        self.assertEqual(member.email, "snoo@whatver.com")
        self.assertEqual(member.address, "somewhere over the rainbow, I guess")
        self.assertEqual(member.posttown, "Town Town Town!")
        self.assertEqual(member.postcode, "< Sixteen chars?")
        self.assertEqual(member.country, "Suriname")
        self.assertEqual(member.website, "http://don't_care/")
        self.assertEqual(member.phone, "+44 0000000000000001")
        self.assertEqual(member.altphone, "-1 3202394 2352 23 234")
        self.assertEqual(member.notes, "plays the balalaika really badly")
        self.assertTrue(member.mailout)
        self.assertTrue(member.is_member)

        # Shouldn't have been changed:
        self.assertEqual(member.mailout_key, member_mailout_key)
        self.assertEqual(
            member.membership_expires,
            datetime.date(day=31, month=5, year=2010),
        )

        self.assertContains(response, new_name)
        self.assertContains(response, "Member 02 updated")

    def test_edit_post_form_invalid_emails(self):
        new_name = "N\u018EW Name"

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, "Tw\u020d Member")
        member_mailout_key = member.mailout_key
        self.assertTrue(member.is_member)

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "name": new_name,
                "email": "definitely_invalid@example/com",
                "k": member_mailout_key,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        self.assertFormError(
            response, "form", "email", "Enter a valid email address."
        )

        member = Member.objects.get(pk=2)
        self.assertNotEqual(member.name, new_name)
        self.assertEqual(member.email, "two@example.com")
        self.assertEqual(member.mailout_key, member_mailout_key)

    def test_edit_post_form_invalid_data_missing(self):
        member = Member.objects.get(pk=2)
        start_name = member.name

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "k": member.mailout_key,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        # Only mandatory field is "name":
        self.assertFormError(
            response, "form", "name", "This field is required."
        )

        member = Member.objects.get(pk=2)
        self.assertEqual(start_name, member.name)

    def test_edit_post_form_no_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url)

        self._assert_redirect_to_login(response, url)

    def test_edit_post_form_incorrect_key(self):
        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "k": "the WRONG KEY",
            },
        )
        self._assert_redirect_to_login(response, url)

    def test_edit_post_form_invalid_memberid(self):
        url = reverse("edit-member", kwargs={"member_id": 21212})
        response = self.client.post(
            url,
            data={
                "k": "the WRONG KEY",
            },
        )
        # If the member doesn't exist then don't give a specific error to that
        # effect, just redirect to the login page:
        self._assert_redirect_to_login(response, url)


class TestEditMemberViewLoggedIn(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestEditMemberViewLoggedIn, self).setUp()
        self.assertTrue(
            self.client.login(username="admin", password="T3stPassword!")
        )

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
    def _test_edit_post_form_minimal_data_common(self):
        new_name = "N\u018EW Name"

        member = Member.objects.get(pk=2)
        self.assertEqual(member.name, "Tw\u020d Member")

        member_mailout_key = member.mailout_key
        membership_expires = member.membership_expires

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "name": new_name,
            },
            follow=True,
        )

        member = Member.objects.get(pk=2)
        # New name set:
        self.assertEqual(member.name, new_name)

        # Secret key shouldn't have been changed:
        self.assertEqual(member.mailout_key, member_mailout_key)

        # Expiry date shouldn't have changed:
        self.assertEqual(member.membership_expires, membership_expires)

        # Should redirect to search page, with a success message inserted:
        self.assertRedirects(response, reverse("search-members"))
        self.assertContains(response, "Member 02 updated")

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    def test_edit_post_form_minimal_data_expiry_enabled(self):
        self._test_edit_post_form_minimal_data_common()

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
    def test_edit_post_form_minimal_data_expiry_disabled(self):
        self._test_edit_post_form_minimal_data_common()

    def _test_edit_post_form_modify_expiry(self, expiry_enabled):
        member = Member.objects.get(pk=2)
        membership_expires = member.membership_expires

        url = reverse("edit-member", kwargs={"member_id": 2})
        self.client.post(
            url,
            data={
                "name": member.name,
                # Always try to set. Should only succeed if expiry is enabled.
                "membership_expires": "01/02/1980",
            },
            follow=True,
        )

        member = Member.objects.get(pk=2)

        # Expiry date shouldn't have changed:
        if expiry_enabled:
            self.assertEqual(
                member.membership_expires, datetime.date(1980, 2, 1)
            )
        else:
            self.assertEqual(member.membership_expires, membership_expires)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    def test_edit_post_modify_expiry_expiry_enabled(self):
        self._test_edit_post_form_modify_expiry(expiry_enabled=True)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=False)
    def test_edit_post_form_modify_expiry_expiry_disabled(self):
        self._test_edit_post_form_modify_expiry(expiry_enabled=False)

    @override_settings(MEMBERSHIP_EXPIRY_ENABLED=True)
    def test_edit_post_form_invalid_data_missing(self):
        member = Member.objects.get(pk=2)
        start_name = member.name

        url = reverse("edit-member", kwargs={"member_id": 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member.html")

        # Only mandatory field is "name":
        self.assertFormError(
            response, "form", "name", "This field is required."
        )

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
            reverse("login")
            + "?next="
            + urllib.parse.quote(url + extra_parameters)
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
        response = self.client.get(
            url,
            data={
                "k": member.mailout_key,
            },
        )

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
        response = self.client.get(
            url,
            data={
                "k": "the WRONG KEY",
            },
        )

        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

        self._assert_subscribed(2)

    def test_unsubscribe_get_form_invalid_memberid(self):
        url = reverse("unsubscribe-member", kwargs={"member_id": 21212})
        response = self.client.get(
            url,
            data={
                "k": "the WRONG KEY",
            },
        )

        # If the member doesn't exist then don't give a specific error to that
        # effect, just redirect to the login page:
        self._assert_redirect_to_login(response, url, "?k=the+WRONG+KEY")

    # POST tests ##########################################
    def test_unsubscribe_post_form(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "k": member.mailout_key,
                "action": "unsubscribe",
                "confirm": "yes",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")
        self.assertContains(response, "Member 02 unsubscribed")

        # Not subscribed:
        self._assert_unsubscribed(2)

    def test_subscribe_post_form(self):
        member = Member.objects.get(pk=2)
        member.mailout = False
        member.save()

        self._assert_unsubscribed(2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "k": member.mailout_key,
                "action": "subscribe",
                "confirm": "yes",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")
        self.assertContains(response, "Member 02 subscribed")

        # subscribed:
        self._assert_subscribed(2)

    def test_unsubscribe_post_form_no_confirm(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "k": member.mailout_key,
                "action": "unsubscribe",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_member_edit_subs.html")
        self.assertNotContains(response, "Member 02 unsubscribed")

        # Still subscribed:
        self._assert_subscribed(2)

    def test_unsubscribe_post_form_invalid_key(self):
        self._assert_subscribed(2)

        member = Member.objects.get(pk=2)

        url = reverse("unsubscribe-member", kwargs={"member_id": 2})
        response = self.client.post(
            url,
            data={
                "k": member.mailout_key + "x",
                "action": "unsubscribe",
                "confirm": "yes",
            },
        )

        self._assert_redirect_to_login(response, url)

        # Still subscribed:
        self._assert_subscribed(2)

    # TODO: Should add further tests for when the user is logged in. But
    # it's not actually used, so don't bother...


class TestMemberMiscViews(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestMemberMiscViews, self).setUp()

        self.assertTrue(
            self.client.login(username="admin", password="T3stPassword!")
        )

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
            '<a href="http://1.foo.test/" '
            'rel="nofollow">http://1.foo.test/</a>',
            html=True,
        )
        self.assertContains(
            response,
            '<a href="http://two.foo.test/" '
            'rel="nofollow">http://two.foo.test/</a>',
            html=True,
        )

    def test_post_homepages(self):
        url = reverse("member-homepages")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)

    def test_view_member(self):
        url = reverse("view-member", kwargs={"member_id": 3})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "view_member.html")
        self.assertContains(response, "Some Third Chap")
        self.assertContains(response, "two@member.test")
        self.assertContains(response, "NORAD")

    def test_view_non_existant_member(self):
        url = reverse("view-member", kwargs={"member_id": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
