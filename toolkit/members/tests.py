import urllib

from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse

import django.contrib.auth.models as auth_models
import django.contrib.contenttypes as contenttypes

from toolkit.members.models import Member, Volunteer
from toolkit.diary.models import Role

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
        m1 = Member(name=u"Member On\u0205", email="one@example.com", number="1", postcode="BS1 1AA")
        m1.save()
        m2 = Member(name=u"Tw\u020d Member", email="two@example.com", number="02", postcode="")
        m2.save()
        m3 = Member(name=u"Some Third Chap", email="two@member.test", number="000", postcode="NORAD")
        m3.save()
        m4 = Member(name="Volunteer One", email="volon@cube.test", number="3",
                    phone="0800 000 000", address="1 Road", posttown="Town", postcode="BS6 123", country="UK",
                    website="http://1.foo.test/")
        m4.save()
        m5 = Member(name="Volunteer Two", email="", number="4",
                    phone="", altphone="", address="", posttown="", postcode="", country="",
                    website="http://two.foo.test/")
        m5.save()
        m6 = Member(name="Volunteer Three", email="volthree@foo.test", number="4",
                    phone="", altphone="", address="", posttown="", postcode="", country="",
                    website="")
        m6.save()

        # Volunteers:
        v1 = Volunteer(member=m4)
        v1.save()
        v1.roles = [r1, r3]
        v1.save()

        v2 = Volunteer(member=m5)
        v2.save()

        v3 = Volunteer(member=m6)
        v3.save()
        v3.roles = [r3]
        v3.save()

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
            'add-volunteer': {'member_id': None, 'create_new': True},
            'view-volunteer-list': {},
            'select-volunteer': {},
            'select-volunteer-inactive': {'active': False},
            'edit-volunteer': {'member_id': 1},
            'activate-volunteer': {},
            'inactivate-volunteer': {'active': False},
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
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_new_member.html")

        member = Member.objects.get(name=new_name)
        self.assertEqual(member.email, u"blah.blah-blah@hard-to-tell-if-genuine.uk")
        self.assertEqual(member.postcode, u"SW1A 1AA")

        self.assertContains(response, u"Added member: {}".format(member.number))

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

        self.assertContains(response,
            u'<form method="get" action="{}"><input type="submit" value="Edit"></form>'.format(
                reverse("edit-member", kwargs={"member_id": 3})),
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


class TestUnsubscribeMemberView(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestUnsubscribeMemberView, self).setUp()
#        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))
#
#    def tearDown(self):
#        self.client.logout()

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


class TestMemberMiscViews(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestMemberMiscViews, self).setUp()

        self.assertTrue(self.client.login(username="admin", password="T3stPassword!"))

    def tearDown(self):
        self.client.logout()

#    def test_get_stats(self):
#        # SQL query for stats doesn't work with SQLite!
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

        self.assertContains(response, u'<a href="http://1.foo.test/" rel="nofollow">http://1.foo.test/</a>', html=True)
        self.assertContains(response, u'<a href="http://two.foo.test/" rel="nofollow">http://two.foo.test/</a>', html=True)

    def test_post_homepages(self):
        url = reverse("member-homepages")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
