from datetime import datetime

from django import template

from confla.models import Timeslot



register = template.Library()

@register.filter
def div(value, arg):
    value = int(value)
    arg = int(arg)
    if arg:
        result = value / arg
        return int(result)
    return ''

