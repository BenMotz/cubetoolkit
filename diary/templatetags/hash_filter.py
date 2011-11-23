from django.template.defaultfilters import register

@register.filter(name='lookup')
def lookup(d, key):
    if key in d:
        return d[key]
    else:
        return ''

