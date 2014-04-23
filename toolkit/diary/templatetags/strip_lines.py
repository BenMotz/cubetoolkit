import re

from django import template

register = template.Library()

multi_blank_line_re = re.compile(ur"(?:^\s*$)+", flags=re.DOTALL | re.MULTILINE)
blank_line_re = re.compile(ur"\n\s*$", flags=re.DOTALL | re.MULTILINE)

# These substitutions would probably be faster using split / filter rather than
# regexes, however as they're currently only used for rendering the member's
# mailout, which doesn't need to be fast, this approach is a bit tidier.

@register.tag(name="filtermultipleblanklines")
def do_filter_multiple_blank_lines(parser, token):
    """
    Filter out multiple blank lines from output
    """
    nodelist = parser.parse(('endfiltermultipleblanklines',))
    parser.delete_first_token()
    return RegexFilterNode(nodelist, multi_blank_line_re)


@register.tag(name="filterblanklines")
def do_filter_blank_lines(parser, token):
    """
    Filter out any blank lines from output
    """
    nodelist = parser.parse(('endfilterblanklines',))
    parser.delete_first_token()
    return RegexFilterNode(nodelist, blank_line_re)


class RegexFilterNode(template.Node):
    """
    Use a supplied regex object to delete content from the rendered output of
    the supplied Node list
    """

    def __init__(self, nodelist, filter_re):
        self.nodelist = nodelist
        self.filter_re = filter_re

    def render(self, context):
        output = self.nodelist.render(context)
        output = self.filter_re.sub('', output)
        return output
