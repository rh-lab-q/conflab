from django.contrib import admin
from confla.models import *
# Register your models here.

class EventAdmin(admin.ModelAdmin):
    list_display = ('topic', 'event_start', 'length', 'is_Scheduled')
    #list_filter = ['event_start']

class RoomAdmin(admin.ModelAdmin):
    #ordering = ('id', 's_name')
    list_display = ('id', 's_name')

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'is_Speaker', 'is_Reviewer')

class PaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'user')

class ConfAdmin(admin.ModelAdmin):
    list_display = ('name', 'conf_start', 'conf_end', 'is_Current')


admin.site.register(Room, RoomAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(EventType)
admin.site.register(Event, EventAdmin)
admin.site.register(Paper, PaperAdmin)
admin.site.register(Conference, ConfAdmin)
