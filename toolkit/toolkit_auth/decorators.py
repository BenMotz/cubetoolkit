from django.contrib.auth.decorators import permission_required


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
