from django.contrib import admin
from conflab.models import *
# Register your models here.

class EventAdmin(admin.ModelAdmin):
    list_display = ('event_start', 'topic')
    #list_filter = ['event_start']

admin.site.register(Room)
admin.site.register(User)
admin.site.register(EventType)
admin.site.register(Event, EventAdmin)
admin.site.register(Paper)
