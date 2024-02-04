# custom_filters.py
from django import template

register = template.Library()

@register.filter(name='urlremove')
def urlremove(value, arg):
    """
    Remove a substring from the value.
    Usage: {{ value|urlremove:"substring" }}
    """
    return value.replace(arg, '', 1)
