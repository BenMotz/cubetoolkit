import logging

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ip_or_permission_required(object):
    """
    Decorator that requires a request to either originate from one of a fixed
    set of IP addresses, or for the request to originate from a logged in user
    with the supplied permissions.
    """
    def __init__(self, ip_addresses, permission):
        self.ip_addresses = ip_addresses
        self.permission = permission

    def __call__(self, function):
        permission_req_wrapper = permission_required(self.permission)(function)

        def wrapper(request, *args, **kwargs):
            if request.META['REMOTE_ADDR'] in self.ip_addresses:
                return function(request, *args, **kwargs)
            else:
                return permission_req_wrapper(request, *args, **kwargs)
        return wrapper


# http://stackoverflow.com/questions/37618473/how-can-i-log-both-successful-and-failed-login-and-logout-attempts-in-django
@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):

    # to cover more complex cases:
    # http://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
    ip = request.META.get('REMOTE_ADDR')
    logger.info('{user} logged in from {ip}'.format(
        user=user,
        ip=ip
    ))


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):

    ip = request.META.get('REMOTE_ADDR')

    logger.info('{user} logged out from {ip}'.format(
        user=user,
        ip=ip
    ))


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, **kwargs):

    logger.warning('login failed for: {credentials}'.format(
        credentials=credentials,
    ))
