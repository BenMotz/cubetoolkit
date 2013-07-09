from django import forms
# Widgety:
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.forms.util import flatatt
from django.utils.encoding import force_unicode


class HtmlTextarea(forms.Textarea):
    """TextArea widget overloaded to provide a wysiwyg HTML editor, using the
    'wysihtml5' editor
    """
    class Media(object):
        # Define media (CSS & JS) used by this control. To include this
        # automatically the template containing the form must have the
        # {{ form.media }} tag
        css = {
            'all': ('css/lib/wysihtml5.css',),
        }
        js = (
            'js/lib/wysihtml5/parser_rules/simple.js',
            'js/lib/wysihtml5/wysihtml5-0.3.0.min.js',
        )

    # Commands available in the editor's toolbar:
    toolbar_commands = (
        # Pair of editor command / toolbar html
        ('bold', 'Bold'),
        ('italic', 'Italic'),
        ('strikethrough', 'Strikethrough'),
        ('superscript', 'Superscript'),
        ('subscript', 'Subscript'),
        ('createLink', 'Insert link'),
        ('insertUnorderedList', 'insertUnorderedList'),
        ('insertOrderedList', 'insertOrderedList'),
    )

    # Generate HTML for the editor control:
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)

        output = [u"<div class='wysihtml5_django_wrapper'><div id='toolbar-{0}' style='display:none;'>"
                  .format(final_attrs['id']), ]
        output.extend(
            u"<a data-wysihtml5-command='{0}'>{1}</a> | "
            .format(cmd, cmdhtml) for (cmd, cmdhtml) in self.toolbar_commands
        )
        output.append(
            "<a data-wysihtml5-action='change_view'>View HTML</a>"
            "<div data-wysihtml5-dialog='createLink' style='display: none;'>"
            "  <label>Link: <input data-wysihtml5-dialog-field='href' value='http://'></label>"
            "  <a data-wysihtml5-dialog-action='save'>OK</a>&nbsp;<a data-wysihtml5-dialog-action='cancel'>Cancel</a>"
            "</div>"
            "</div>"
        )
        output.append(u'<textarea{0}>{1}</textarea>'.format(
            flatatt(final_attrs),
            conditional_escape(force_unicode(value))
        ))
        output.append(
            u"</div>"
            "<script type='text/javascript'>"
            " var editor = new wysihtml5.Editor('{0}', {{"
            "   toolbar:      'toolbar-{0}',"
            "   parserRules:  wysihtml5ParserRules"
            " }});"
            "</script>".format(final_attrs['id'])
        )

        return mark_safe(u'\n'.join(output))


class JQueryDateTimePicker(forms.DateTimeInput):
    """
    Override DateTimeInput form widget to automatically use the JQueryUI
    control
    """
    def __init__(self, *args, **kwargs):
        # Change the default date/time format to match that used by the
        # jquery widget (which is also the more conventional UK format)
        if 'format' not in kwargs:
            kwargs['format'] = "%d/%m/%Y %H:%M"

        super(JQueryDateTimePicker, self).__init__(*args, **kwargs)

    class Media(object):
        css = {
            'all': ('css/lib/smoothness/jquery-ui.css', 'css/lib/timepicker.css', ),
        }
        js = (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/lib/jquery-ui-timepicker-addon.js',
        )

    def render(self, name, value, attrs=None):
        # Use the default rendering (a textbox) :
        output = super(JQueryDateTimePicker, self).render(name, value, attrs=attrs)

        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)

        # Add JS code to attach the JQuery UI code and make the "magic" happen.
        # Note that the (hardcoded) dateFormat/timeFormat match that set for
        # the textbox in __init__
        output += (u"<script type='text/javascript'>"
                   "$('#{control_id}').datetimepicker({{ "
                   "dateFormat : 'dd/mm/yy', timeFormat : 'hh:mm', minDate : 0"
                   "}});"
                   "</script>".format(control_id=final_attrs[u'id']))

        return mark_safe(output)
