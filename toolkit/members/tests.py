from django.test import TestCase
from django.core.urlresolvers import reverse

from toolkit.members.models import Member, Volunteer

class SecurityTests(TestCase):
    """Basic test that the private pages do not load without a login"""

    fixtures = ['small_data_set.json']

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


class TestVolunteerEditViews(TestCase):

    fixtures = ['small_data_set.json']

    def setUp(self):
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


