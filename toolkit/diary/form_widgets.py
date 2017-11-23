from django import forms


class ChosenSelectMultiple(forms.SelectMultiple):
    """
    SelectMultiple widget using the "Chosen" jquery plugin:
    http://harvesthq.github.io/chosen/
    """

    template_name = 'widgets/chosenselectmultiple.html'

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

    def get_context(self, name, value, attrs):
        context = super(ChosenSelectMultiple, self).get_context(
            name, value, attrs)
        context['widget'].update({
            'width': self.width,
        })
        return context


class HtmlTextarea(forms.Textarea):
    """TextArea widget overloaded to provide a wysiwyg HTML editor, using the
    'CKEditor' editor
    """

    template_name = 'widgets/htmltextarea.html'

    class Media(object):
        # Define media (CSS & JS) used by this control. To include this
        # automatically the template containing the form must have the
        # {{ form.media }} tag
        js = (
            'js/lib/ckeditor/ckeditor.js',
        )

    def __init__(self, *args, **kwargs):
        self.enable_tables = kwargs.pop('enable_tables', False)
        self.enable_iframes = kwargs.pop('enable_iframes', True)
        self.height = kwargs.pop('height', None)
        super(HtmlTextarea, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super(HtmlTextarea, self).get_context(name, value, attrs)
        context['widget']['enable_tables'] = self.enable_tables
        context['widget']['enable_iframes'] = self.enable_iframes
        if self.height:
            context['widget']['height'] = self.height
        return context


class JQueryDateTimePicker(forms.DateTimeInput):
    """
    Override DateTimeInput form widget to automatically use the JQueryUI
    control
    """

    template_name = 'widgets/jquerydatetimepicker.html'

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
