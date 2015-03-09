from django.contrib import admin
from confla.models import *
# Register your models here.

class EventAdmin(admin.ModelAdmin):
    list_display = ('event_start', 'topic')
    #list_filter = ['event_start']

class RoomAdmin(admin.ModelAdmin):
    #ordering = ('id', 's_name')
    list_display = ('id', 's_name')

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'name')

class PaperAdmin(admin.ModelAdmin):
    list_display = ('user', 'title')

class ConfAdmin(admin.ModelAdmin):
    list_display = ('name', 'conf_start', 'conf_end')


admin.site.register(Room, RoomAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(EventType)
admin.site.register(Event, EventAdmin)
admin.site.register(Paper, PaperAdmin)
admin.site.register(Conf, ConfAdmin)
