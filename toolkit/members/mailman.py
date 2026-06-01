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


def get_lists(client: Client) -> dict[str, MailingList]:
    lists: dict[str, MailingList] = {}
    for list_name in settings.MAILMAN_VOLUNTEER_LISTS:
        try:
            lists[list_name] = client.get_list(list_name)
        except (MailmanConnectionError, urllib.error.HTTPError) as err:
            raise MailmanError(
                f"Failed retrieiving list info from Mailman for list {list_name}: {err}"
            )
    return lists


def get_lists_members() -> dict[str, set[str]]:
    # Returns a map of list_name to the set of subscribed email addresses
    client = try_connect()
    lists = get_lists(client)

    return {
        list_name: set(member.email.lower() for member in list_data.members if member)
        for list_name, list_data in lists.items()
    }


def subscribe_volunteer(name: str, email: str) -> Optional[str]:
    lists: dict[str, MailingList] = {}
    errors: list[str] = []
    try:
        client = try_connect()
    except MailmanError as err:
        logger.error(f"Failed connecting to Mailman: {err}")
        return "could not connect to Mailman"

    try:
        lists = get_lists(client)
    except MailmanError as me:
        logger.error(str(me))
        return "could not retrieve list data from Mailman"

    for list_name, list_inst in lists.items():
        try:
            response = list_inst.subscribe(
                address=email,
                display_name=name,
                pre_approved=True,  # Skip list admin approval step
                pre_confirmed=True,  # Skip subscriber confirmation step (i.e. no "reply to this to confirm you really want to join the list")
                pre_verified=True,  # Assert that the email address is valid (i.e. no "reply to this to confirm this address exists" step)
            )
        except (MailmanConnectionError, urllib.error.HTTPError) as err:
            logger.error(
                f"Failed telling Mailman to subscribe {email} to {list_name}: {err}"
            )
            errors.append(f"subscribe operation failed for {list_name}")
        else:
            if not isinstance(response, Member):
                logger.info(
                    f"Mailman is unexpectedly waiting for confirmation for subscription request for {email} to {list_name}: {response}"
                )
                errors.append(
                    f"subscription to {list_name} waiting for approval and/or email verification"
                )

    logger.info(f"Subscribed {name} <{email}> to {', '.join(lists.keys())}")
    if len(errors) > 0:
        return "; ".join(errors)
    return None


def unsubscribe_volunteer(email: str) -> Optional[str]:
    try:
        client = try_connect()
    except MailmanError as err:
        logger.error(f"Failed connecting to Mailman: {err}")
        return "could not connect to Mailman"

    try:
        lists = get_lists(client)
    except MailmanError as me:
        logger.error(str(me))
        return "could not retrieve list data from Mailman"

    errors = []
    for list_name, list_inst in lists.items():
        try:
            list_inst.unsubscribe(
                email=email,
                pre_confirmed=True,  # unsub is aproved by the user
                pre_approved=True,  # unsub is approved by the moderator
            )
        except (MailmanConnectionError, urllib.error.HTTPError) as err:
            logger.error(
                f"Failed telling Mailman to unsubscribe {email} to {list_name}: {err}"
            )
            errors.append(f"unsubscribe operation failed for {list_name}")
        except ValueError as ve:
            logger.error(
                f"Failed telling Mailman to unsubscribe {email} to {list_name}: {ve}"
            )
            errors.append(f"{email} is not subscribed to {list_name}")

    if len(errors) > 0:
        return "; ".join(errors)

    logger.info(f"Unsubscribed {email} from {', '.join(lists.keys())}")
    return None
