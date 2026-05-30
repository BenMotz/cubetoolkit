from unittest.mock import patch, call, PropertyMock, MagicMock

from django.test import SimpleTestCase, override_settings
from mailmanclient import MailmanConnectionError, Member

import toolkit.members.mailman as mailman

VOLUNTEER_LISTS = ["volunteers@cubecinema.com", "rota@cubecinema.com"]


@override_settings(MAILMAN_VOLUNTEER_LISTS=VOLUNTEER_LISTS)
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
        self.mailman_mock.return_value.get_list.assert_has_calls(
            [call(list_name) for list_name in VOLUNTEER_LISTS]
        )
        self.mailman_mock.return_value.get_list.return_value.subscribe.assert_called_with(
            address="example@bobson.com",
            display_name="Bob bobsen",
            pre_approved=True,
            pre_confirmed=True,
            pre_verified=True,
        )
        self.assertEqual(
            self.mailman_mock.return_value.get_list.return_value.subscribe.call_count,
            len(VOLUNTEER_LISTS),
        )
        self.assertIsNone(result)

    def test_unsubscribe(self):
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.mailman_mock.return_value.get_list.assert_has_calls(
            [call(list_name) for list_name in VOLUNTEER_LISTS]
        )
        self.mailman_mock.return_value.get_list.return_value.unsubscribe.assert_called_with(
            email="example@bobson.com",
            pre_approved=True,
            pre_confirmed=True,
        )
        self.assertEqual(
            self.mailman_mock.return_value.get_list.return_value.unsubscribe.call_count,
            len(VOLUNTEER_LISTS),
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
        self.assertEqual("could not retrieve list data from Mailman", result)

    def test_subscribe_suprise_token(self):
        self.mailman_mock.return_value.get_list.return_value.subscribe.return_value = {
            "token": "I guess"
        }
        result = mailman.subscribe_volunteer(name="Rob", email="e@example.com")
        self.assertEqual(
            "subscription to volunteers@cubecinema.com waiting for approval and/or email verification; "
            "subscription to rota@cubecinema.com waiting for approval and/or email verification",
            result,
        )

    def test_subscribe_fail(self):
        self.mailman_mock.return_value.get_list.return_value.subscribe.side_effect = MailmanConnectionError(
            "waa"
        )
        result = mailman.subscribe_volunteer(
            name="Bob bobsen", email="example@bobson.com"
        )
        self.assertEqual(
            result,
            "subscribe operation failed for volunteers@cubecinema.com; "
            "subscribe operation failed for rota@cubecinema.com",
        )

    def _patch_subscribe_per_list(
        self, behaviour_by_list: dict[str, object]
    ) -> dict[str, MagicMock]:
        list_mocks = {}

        for list_name, behaviour in behaviour_by_list.items():
            list_mock = MagicMock()
            if isinstance(behaviour, Exception):
                list_mock.subscribe.side_effect = behaviour
            else:
                list_mock.subscribe.return_value = behaviour
            list_mocks[list_name] = list_mock

        self.mailman_mock.return_value.get_list.side_effect = (
            list_mocks.__getitem__
        )
        return list_mocks

    def test_subscribe_partial_failure(self) -> None:
        self._patch_subscribe_per_list(
            {
                "volunteers@cubecinema.com": Member("", ""),
                "rota@cubecinema.com": MailmanConnectionError("waargh"),
            }
        )
        result = mailman.subscribe_volunteer(
            name="Bob Bobsen", email="bobson@example.com"
        )
        self.assertEqual(
            result,
            "subscribe operation failed for rota@cubecinema.com",
        )

    def test_subscribe_mixed_errors(self) -> None:
        self._patch_subscribe_per_list(
            {
                "volunteers@cubecinema.com": MailmanConnectionError("eek!"),
                "rota@cubecinema.com": {"token": "I guess"},
            }
        )
        result = mailman.subscribe_volunteer(
            name="Bob Bobsen", email="bobson@example.com"
        )
        self.assertEqual(
            result,
            "subscribe operation failed for volunteers@cubecinema.com; "
            "subscription to rota@cubecinema.com waiting for approval and/or email verification",
        )

    def test_unsubscribe_fail(self):
        self.mailman_mock.return_value.get_list.return_value.unsubscribe.side_effect = MailmanConnectionError(
            "boo"
        )
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.assertEqual(
            result,
            "unsubscribe operation failed for volunteers@cubecinema.com; "
            "unsubscribe operation failed for rota@cubecinema.com",
        )

    def test_unsubscribe_fail_unknown_user(self):
        self.mailman_mock.return_value.get_list.return_value.unsubscribe.side_effect = ValueError(
            ":-("
        )
        result = mailman.unsubscribe_volunteer(email="example@bobson.com")
        self.assertEqual(
            result,
            "example@bobson.com is not subscribed to volunteers@cubecinema.com; "
            "example@bobson.com is not subscribed to rota@cubecinema.com",
        )
