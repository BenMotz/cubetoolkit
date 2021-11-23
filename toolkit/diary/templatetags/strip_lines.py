from django import template

register = template.Library()

# This was originally implemented using much simpler regexes, but they didn't
# work right in Python 2.6. Stupid Python 2.6. No longer shackled to 2.6, so
# could revisit this, but life's too short.


@register.tag(name="filtermultipleblanklines")
def do_filter_multiple_blank_lines(parser, token):
    """
    Filter out multiple blank lines from output
    """
    nodelist = parser.parse(("endfiltermultipleblanklines",))
    parser.delete_first_token()
    return MultiBlankLineFilterNode(nodelist)


class MultiBlankLineFilterNode(template.Node):
    """
    Replace repeated blank lines in rendered output of supplied nodelist with
    a single blank line
    """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        filtered_lines = []

        for line in output.split(u"\n"):
            line = line.rstrip()
            if filtered_lines and filtered_lines[-1] == u"" and line == u"":
                pass
            else:
                filtered_lines.append(line)

        return u"\n".join(filtered_lines)


@register.tag(name="filterblanklines")
def do_filter_blank_lines(parser, token):
    """
    Filter out any blank lines from output
    """
    nodelist = parser.parse(("endfilterblanklines",))
    parser.delete_first_token()
    return BlankLineFilterNode(nodelist)


class BlankLineFilterNode(template.Node):
    """
    Delete all blank lines from rendered output of supplied nodelist
    """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        output = u"\n".join(
            [line for line in output.split(u"\n") if line.strip() != ""]
        )
        return output
