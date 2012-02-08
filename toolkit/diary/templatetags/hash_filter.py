from django.template.defaultfilters import register
"""Simple filter for use in django templates that allows extraction of a given
key from a dictionary"""

@register.filter(name='lookup')
def lookup(d, key):
    if key in d:
        return d[key]
    else:
        return ''

