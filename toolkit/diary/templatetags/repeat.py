from django import template

register = template.Library()


class CaptureNode(template.Node):
    # Render provided set of nodes, and store the rendered output for
    # retrieval.
    def __init__(self, nodelist):
        self._nodelist = nodelist
        self.capture = ""

    def render(self, context):
        rendered = self._nodelist.render(context)
        self.capture = rendered
        return rendered


@register.tag(name="capture")
def do_capture(parser, token):
    """
    Capture some content
    """
    try:
        tag_name, capture_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    nodelist = parser.parse(('endcapture',))
    parser.delete_first_token()

    node = CaptureNode(nodelist)

    # Store a reference to the capturing node, under the given name
    try:
        parser._captured
    except AttributeError:
        parser._captured = {}
    parser._captured[capture_name] = node

    return node


class CaptureRetrieverNode(template.Node):
    # Store a reference to an instance of CaptureNode, then when rendering use
    # its captured content.
    def __init__(self, capturing_node):
        self._capturing_node = capturing_node

    def render(self, context):
        return self._capturing_node.capture


@register.tag(name="retrieve")
def do_retrieve(parser, token):
    """
    Repeat some captured content
    """
    try:
        tag_name, capture_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )

    try:
        capturing_node = parser._captured[capture_name]
    except KeyError:
        raise template.TemplateSyntaxError(
            "'%s' tag trying to retrieve non-existent capture '%s'" %
            (tag_name, capture_name))

    return CaptureRetrieverNode(capturing_node)
