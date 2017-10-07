from django import forms
# Widgety:
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.forms.utils import flatatt
from django.utils.encoding import force_text


class ChosenSelectMultiple(forms.SelectMultiple):
    """
    SelectMultiple widget using the "Chosen" jquery plugin:
    http://harvesthq.github.io/chosen/
    """
    class Media(object):
        # Define media (CSS & JS) used by this control. To include this
        # automatically the template containing the form must have the
        # {{ form.media }} tag
        js = (
            'js/lib/jquery.min.js',
            'js/lib/chosen.jquery.js',
        )
        css = {
            'all': ('css/lib/chosen.min.css',),
        }

    def __init__(self, *args, **kwargs):
        self.width = kwargs.pop('width', None)
        super(ChosenSelectMultiple, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        # Use the default rendering:
        output = super(ChosenSelectMultiple, self).render(
            name, value, attrs=attrs, choices=choices)

        final_attrs = self.build_attrs(attrs, name=name)

        if self.width:
            options = "{width: '%s'}" % self.width
        else:
            options = "{}"

        # Add JS code to get the "Chosen" library to do the setup
        output += (u"<script type='text/javascript'>"
                   "$('#{control_id}').chosen({options});"
                   "</script>".format(
                       control_id=final_attrs[u'id'],
                       options=options
                   ))

        return mark_safe(output)


class HtmlTextarea(forms.Textarea):
    """TextArea widget overloaded to provide a wysiwyg HTML editor, using the
    'CKEditor' editor
    """
    class Media(object):
        # Define media (CSS & JS) used by this control. To include this
        # automatically the template containing the form must have the
        # {{ form.media }} tag
        js = (
            'js/lib/ckeditor/ckeditor.js',
        )

    # Generate HTML for the editor control:
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''

        final_attrs = self.build_attrs(attrs, name=name)

        output = [
            u"<div class='ckeditor_django_wrapper'>",
            u'<textarea{0}>{1}</textarea>'.format(
                flatatt(final_attrs),
                conditional_escape(force_text(value))
            ),
            u"</div>",
            u"<script type='text/javascript'>",
            u" CKEDITOR.replace('{0}');".format(
                final_attrs['id']
            ),
            u"</script>",
        ]

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
            'all': ('css/lib/smoothness/jquery-ui.css',
                    'css/lib/timepicker.css', ),
        }
        js = (
            'js/lib/jquery.min.js',
            'js/lib/jquery-ui.min.js',
            'js/lib/jquery-ui-timepicker-addon.js',
        )

    def render(self, name, value, attrs=None):
        # Use the default rendering (a textbox) :
        output = super(JQueryDateTimePicker, self).render(
            name, value, attrs=attrs)

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
