from typing import Optional, Any
import logging
import urllib.error

from django.conf import settings
from mailmanclient import Client, MailmanConnectionError, Member, MailingList


logger = logging.getLogger(__name__)


class MailmanError(Exception):
    pass


def _set_timeout(params: dict[str, Any]) -> dict[str, Any]:
    params["timeout"] = settings.MAILMAN_TIMEOUT_SECONDS
    return params


def try_connect() -> Client:

    if not settings.MAILMAN_INTEGRATION:
        raise MailmanError("Mailman integration disabled")
    client = Client(
        baseurl=settings.MAILMAN_URL,
        name=settings.MAILMAN_API_USER,
        password=settings.MAILMAN_API_KEY,
        request_hooks=[_set_timeout],
    )

    # Check the connection by reading the system version
    try:
        client.system
    except MailmanConnectionError as mce:
        raise MailmanError("".join(mce.args)) from mce
    except urllib.error.HTTPError as hte:
        raise MailmanError(
            f"HTTP status {hte.status} connecting to {hte.filename}: {hte.msg}"
        )
    return client


def get_volunteer_list() -> MailingList:
    client = try_connect()

    try:
        return client.get_list(settings.MAILMAN_VOLUNTEER_LIST)
    except (MailmanConnectionError, urllib.error.HTTPError) as err:
        raise MailmanError(
            f"Failed retrieiving list info from Mailman for {settings.MAILMAN_VOLUNTEER_LIST}: {err}"
        )


def subscribe_volunteer(name: str, email: str) -> Optional[str]:
    try:
        volunteer_list = get_volunteer_list()
    except MailmanError as me:
        logger.error(f"Failed connecting to mailman: {me}")
        return "Failed connecting to Mailman"

    try:
        response = volunteer_list.subscribe(
            address=email,
            display_name=name,
            pre_approved=True,  # Skip list admin approval step
            pre_confirmed=True,  # Skip subscriber confirmation step (i.e. no "reply to this to confirm you really want to join the list")
            pre_verified=True,  # Assert that the email address is valid (i.e. no "reply to this to confirm this address exists" step)
        )
    except (MailmanConnectionError, urllib.error.HTTPError) as err:
        logger.error(
            f"Failed telling Mailman to subscribe {email} to {settings.MAILMAN_VOLUNTEER_LIST}: {err}"
        )
        return "Failed subscribing volunteer to list"

    if not isinstance(response, Member):
        logger.info(
            f"Mailman is unexpectedly waiting for confirmation for subscription request for {email}: {response}"
        )
        return "Subscription waiting for approval and/or email verification"

    logger.info(
        f"Subscribed {name} <{email}> to {settings.MAILMAN_VOLUNTEER_LIST}"
    )
    return None


def unsubscribe_volunteer(email: str) -> Optional[str]:
    try:
        volunteer_list = get_volunteer_list()
    except MailmanError as me:
        logger.error(f"Failed connecting to mailman: {me}")
        return "Failed connecting to Mailman"

    try:
        volunteer_list.unsubscribe(
            email=email,
            pre_confirmed=True,  # unsub is aproved by the user
            pre_approved=True,  # unsub is approved by the moderator
        )
    except (MailmanConnectionError, urllib.error.HTTPError) as err:
        logger.error(
            f"Failed telling Mailman to unsubscribe {email} to {settings.MAILMAN_VOLUNTEER_LIST}: {err}"
        )
        return "Failed unsubscribing volunteer from the volunteer's list"
    except ValueError as ve:
        logger.error(
            f"Failed telling Mailman to unsubscribe {email} to {settings.MAILMAN_VOLUNTEER_LIST}: {ve}"
        )
        return f"Failed unsubscribing volunteer from the volunteer's list: {email} is not subscribed"

    logger.info(f"Unsubscribed {email} from {settings.MAILMAN_VOLUNTEER_LIST}")
    return None
