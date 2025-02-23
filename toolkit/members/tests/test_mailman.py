from unittest.mock import patch, PropertyMock

from django.test import SimpleTestCase
from mailmanclient import MailmanConnectionError, Member

import toolkit.members.mailman as mailman


class TestSubscribeVolunteer(SimpleTestCase):
    def setUp(self):
        self.mailmanclient_patch = patch("toolkit.members.mailman.Client")
        self.mailman_mock = self.mailmanclient_patch.start()
        self.mailman_mock.client
        self.addCleanup(self.mailmanclient_patch.stop)

    def test_subscribe(self):
        self.mailman_mock.return_value.get_list.return_value.subscribe.return_value = Member(
            "", ""
        )

        result = mailman.subscribe_volunteer(
            name="Bob bobsen", email="example@bobson.com"
        )
        self.mailman_mock.return_value.get_list.assert_called_once_with(
            "volunteers@cubecinema.com"
        )
        self.mailman_mock.return_value.get_list.return_value.subscribe.assert_called_once_with(
            address="example@bobson.com",
            display_name="Bob bobsen",
            pre_approved=True,
            pre_confirmed=True,
            pre_verified=True,
        )
        self.assertIsNone(result)

    def test_unsubscribe(self):
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.mailman_mock.return_value.get_list.assert_called_once_with(
            "volunteers@cubecinema.com"
        )
        self.mailman_mock.return_value.get_list.return_value.unsubscribe.assert_called_once_with(
            email="example@bobson.com",
            pre_approved=True,
            pre_confirmed=True,
        )
        self.assertIsNone(result)

    def test_connect_fail(self):
        type(self.mailman_mock.return_value).system = PropertyMock(
            side_effect=MailmanConnectionError("foo")
        )

        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.assertEqual(result, "could not connect to Mailman")

    def test_get_list_fail(self):
        self.mailman_mock.return_value.get_list.side_effect = (
            MailmanConnectionError("boom")
        )
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.assertEqual("could not connect to Mailman", result)

    def test_subscribe_suprise_token(self):
        self.mailman_mock.return_value.get_list.return_value.subscribe.return_value = {
            "token": "I guess"
        }
        result = mailman.subscribe_volunteer(name="Rob", email="e@example.com")
        self.assertEqual(
            "Subscription waiting for approval and/or email verification",
            result,
        )

    def test_subscribe_fail(self):
        self.mailman_mock.return_value.get_list.return_value.subscribe.side_effect = MailmanConnectionError(
            "waa"
        )
        result = mailman.subscribe_volunteer(
            name="Bob bobsen", email="example@bobson.com"
        )
        self.assertEqual(result, "subscribe operation failed")

    def test_unsubscribe_fail(self):
        self.mailman_mock.return_value.get_list.return_value.unsubscribe.side_effect = MailmanConnectionError(
            "boo"
        )
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.assertEqual(result, "unsubscribe operation failed")

    def test_unsubscribe_fail_unknown_user(self):
        self.mailman_mock.return_value.get_list.return_value.unsubscribe.side_effect = ValueError(
            ":-("
        )
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.assertEqual(result, "example@bobson.com is not subscribed")
