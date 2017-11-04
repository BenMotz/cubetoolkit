from __future__ import print_function

from django.test import TestCase
from django.core.urlresolvers import reverse

from toolkit.members.models import Member

from .common import MembersTestsMixin


class SecurityTests(MembersTestsMixin, TestCase):
    """Basic test that the private pages do not load without a login"""

    write_required = {
        # Volunteer urls:
        'add-volunteer': {},
        'edit-volunteer': {'volunteer_id': 1},
        'activate-volunteer': {},
        'inactivate-volunteer': {},
        'add-volunteer-training-group-record': {},
        'add-volunteer-training-record': {'volunteer_id': 1},
        'delete-volunteer-training-record': {'training_record_id': 1},
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
        'view-volunteer-training-report': {},
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
