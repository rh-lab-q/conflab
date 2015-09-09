from datetime import datetime

from django import template

from confla.models import Event, Timeslot, Conference
from confla.forms import EventCreateForm, EventEditForm


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
def get_event_form(value):
    form = EventCreateForm(instance=value)
    return form

@register.filter
def tag_class(value):
    return "tag" + str(value.prim_tag.id) if value.prim_tag else "tag0"

@register.filter
def set_height(value, arg):
    size = int(arg)
    return str(size*value-2) + "px" # 2 is border size in pixels

@register.inclusion_tag('confla/event_modal.html')
def include_modal(event=None):
    if event:
        form = EventEditForm(instance=event)
        return { 'form' : form, 'event' : event }

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
