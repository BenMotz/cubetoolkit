"""Simple filter for use in django templates that allows extraction of a given
key from a dictionary"""

from django.template.defaultfilters import register

@register.filter(name='lookup')
def lookup(dictionary, key):
    """Simple filter for use in django templates that allows extraction of a 
    given key from a dictionary"""
    if key in dictionary:
        return dictionary[key]
    else:
        return ''

