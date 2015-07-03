from datetime import datetime

from django import template

from confla.models import Event, Timeslot, Conference
from confla.forms import EventCreateForm


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
def get_slots(value, arg):
    slot_list = []
    slots = Timeslot.objects.filter(conf_id=Conference.get_active())
    for s in slots:
        if s.get_start_datetime == arg['full']:
            slot_list.append(s)
    return slot_list

@register.filter
def get_event_form(value):
    form = EventCreateForm(instance=value)
    return form

@register.filter
def tag_class(value):
    return "tag" + str(value.tags.all()[0].id)

@register.filter
def set_height(value, arg):
    size = int(arg)
    return str(size*value) + "px"

"""
@register.filter
def is_free(value, arg):
    slots = Timeslot.objects.filter(room_id=value['room'], conf_id=value['conf'])
    time = datetime.strptime(arg['full'], '%x %H:%M')
    for s in slots:
        if datetime.strptime(s.get_start_datetime, '%x %H:%M') < time and datetime.strptime(s.get_end_datetime, '%x %H:%M') > time:
            return False
    return True
"""
