from django.template import Library, Context
from django.template.loader import get_template


register = Library()


@register.filter(name="to_crispy_field")
def to_crispy_field(field):
    template = get_template("bootstrap4/field.html")
    return template.render(
        Context(
            {
                "field": field,
                "form_show_errors": True,
                "form_show_labels": False,
            }
        ).flatten()
    )
