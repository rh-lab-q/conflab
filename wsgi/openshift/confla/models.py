from datetime import datetime, timedelta, date

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

from confla.utils import *

class Conference(models.Model):
    name = models.CharField(max_length=256)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    # Returns a list of times during a day for a defined timedelta
    def get_delta_list(self):
        def delta_func(start, end, delta):
            current = start
            while current < end:
                yield current
                current = (datetime.combine(date.today(), current) + delta).time()

        mins = settings.TIMEDELTA
        delta_list = [x.strftime("%H:%M") for x in delta_func(self.start_time,
                                                                self.end_time,
                                                                timedelta(minutes=mins))]
        return delta_list
#    def is_Current(self):
#        return (self.end_date and self.start_date) and (self.end_date > timezone.now())

    # gets events in a conference, filter by speaker, room, type
    def get_Events(self, speaker_id=None, room_id=None, type_id=None):
        event_set = Event.objects.filter(conf=self.id)
        if speaker_id:
            event_set = event_set.filter(speaker=speaker_id)
        if room_id:
            event_set = event_set.filter(room=room_id)
        if type_id:
            event_set = event_set.filter(e_type=type_id)
        return event_set

class Room(models.Model):
    shortname = models.CharField(max_length=16)
    name = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=8, blank=True)
    conf_id = models.ForeignKey(Conference)

    def __str__(self):
        return self.shortname

class ConflaUser(AbstractUser):
    # name = models.CharField(max_length=32)
    phone = models.CharField(max_length=32, blank=True)
    picture = models.ImageField(upload_to=user_rename_and_return_path('avatars/'),
                                blank=True, null=True)
    company = models.CharField(max_length=256, blank=True)
    position = models.CharField(max_length=256, blank=True)
    web = models.URLField(max_length=512, blank=True)
    facebook = models.URLField(max_length=512, blank=True)
    twitter = models.URLField(max_length=512, blank=True)
    google_plus = models.URLField(max_length=512, blank=True)
    linkedin = models.URLField(max_length=512, blank=True)
    bio = models.TextField (blank=True)
    schedule = models.ManyToManyField('Event', related_name='sched+', blank=True, null=True)

    def __str__(self):
        return self.username

    def is_Speaker(self):
        return len(Event.objects.filter(speaker=self.username)) != 0

    def is_Reviewer(self):
        return len(Paper.objects.filter(reviewer=self.username)) != 0

    class Meta:
        permissions = (
            ("can_volunteer", "Is a volunteer in a Conference"),
            ("can_organize", "Is an organizer in a Conference"),
        )

class VolunteerBlock(models.Model):
    name =  models.CharField(max_length=256)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    room_id = models.ForeignKey(Room, blank=True, null=True)
    max_volunteers = models.IntegerField()

    def __str__(self):
        return self.name

class Volunteer(models.Model):
    user = models.OneToOneField(ConflaUser, primary_key=True)
    volunteer_block_id = models.ManyToManyField(VolunteerBlock, related_name='block+')

    def __str__(self):
        return self.user.username

class EmailAdress(models.Model):
    user = models.ForeignKey(ConflaUser)
    address = models.EmailField(max_length=256, unique=True)
    is_active = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.address

    @property
    def is_primary(self):
        return self.user.email == self.address

class EventTag(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

class EventType(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

class Event(models.Model):
    conf_id = models.ForeignKey(Conference)
    e_type_id = models.ForeignKey(EventType)
    topic = models.CharField(max_length=256)
    description = models.TextField()
    lang = models.CharField(max_length=6)
    slides = models.URLField(max_length=512, blank=True)
    video = models.URLField(max_length=512, blank=True)
    google_doc_url = models.URLField(max_length=512, blank=True)
    speaker = models.ManyToManyField(ConflaUser, related_name='usr+')
    tags = models.ManyToManyField(EventTag, related_name='tag+', blank=True, null=True)

    def __str__(self):
        return self.topic

    #def is_Scheduled(self):
    #    return (self.event_start != None) and (self.event_end != None)

class Timeslot(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    room_id = models.ForeignKey(Room, blank=True, null=True)
    event_id = models.OneToOneField(Event, blank=True, null=True)
    conf_id = models.ForeignKey(Conference)

    @property
    def get_start_time(self):
        return self.start_time.time().strftime("%H:%M")

    @property
    def get_end_time(self):
        return self.end_time.time().strftime("%H:%M")


    # event length in minutes
    @property
    def length(self):
        if self.start_time and self.end_time:
            return round((self.end_time - self.start_time).seconds / 60)

class Paper(models.Model):
    user = models.ForeignKey(ConflaUser)
    title = models.CharField(max_length=256)
    abstract = models.TextField()
    source = models.FileField(upload_to=paper_rename_and_return_path('papers/'),
                                blank=True, null=True,
                                validators=[validate_papers])
    accepted = models.NullBooleanField()
    reviewer = models.ManyToManyField(ConflaUser, related_name='rev+', blank=True, null=True)

    def __str__(self):
        return self.title
