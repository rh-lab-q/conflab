import os
from datetime import datetime

from django import template
from PIL import Image
from PIL import ImageOps

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

def resized_path(path, size):
    "Returns the path for the resized image."

    dir, name = os.path.split(path)
    image_name, ext = name.rsplit('.', 1)
    return os.path.join(dir, '%s_%s.%s' % (image_name, size, 'jpg'))

@register.filter
def scale(imagefield, size, method='scale'):
    image_path = resized_path(imagefield.path, size)

    if not os.path.exists(image_path):
        image = Image.open(imagefield.path)

        # normalize image mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # parse size string 'WIDTHxHEIGHT'
        width, height = [int(i) for i in size.split('x')]

        # use PIL methods to edit images
        if method == 'scale':
            image.thumbnail((width, height), Image.ANTIALIAS)
            image.save(image_path, 'JPEG', quality=95)

        elif method == 'crop':
            ImageOps.fit(image, (width, height), Image.ANTIALIAS
                        ).save(image_path, 'JPEG', quality=95)

    return resized_path(imagefield.url, size)


@register.filter
def crop(imagefield, size):
    return scale(imagefield, size, 'crop')

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
