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

@register.filter
def get_slot(value, arg):
    slots = Timeslot.objects.filter(room_id=value.id)
    for s in slots:
        if s.get_start_time == arg:
            return s
    return False

@register.filter
def is_free(value, arg):
    slots = Timeslot.objects.filter(room_id=value.id)
    time = datetime.strptime(arg, "%H:%M")
    for s in slots:
        if datetime.strptime(s.get_start_time, "%H:%M") < time and datetime.strptime(s.get_end_time, "%H:%M") > time:
            return False
    return True
