import logging
import urlparse

from django import template
from django.template.defaulttags import url, URLNode
from django.core.urlresolvers import get_script_prefix

register = template.Library()
logger = logging.getLogger(__name__)

class NoPrefixURLNode(URLNode):
    def __init__(self, url_node):
        super(NoPrefixURLNode, self).__init__(url_node.view_name, url_node.args, url_node.kwargs, url_node.asvar)

    def render(self, context):
        text = super(NoPrefixURLNode, self).render(context)
        prefix = get_script_prefix()

        parts = urlparse.urlsplit(text)

        if not parts.path.startswith(prefix):
            logger.error("Path %s doesn't start with prefix %s", text, prefix)

        new_parts = list(parts)
        new_parts[2] = parts.path[len(prefix) - 1:]
        return urlparse.urlunsplit(new_parts)


@register.tag
def noprefix_url(parser, token):
    """
    Returns an absolute URL matching given view with its parameters, with any
    path prefix from the WSGI request stripped.
    """
    return NoPrefixURLNode(url(parser, token))
