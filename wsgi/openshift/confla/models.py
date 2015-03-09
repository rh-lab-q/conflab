import datetime
from django.db import models
from django.utils import timezone

class Conference(models.Model):
    name = models.CharField(max_length=256)
    conf_start = models.DateTimeField(blank=True, null=True)
    conf_end = models.DateTimeField(blank=True, null=True)
    datetime.timedelta(days=1)
    def __str__(self):
        return self.name
    def is_Current(self):
        return (self.conf_end == self.conf_start != None) and (self.conf_end > timezone.now())

class Room(models.Model):
    s_name = models.CharField(max_length=16)
    name = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=8)
    conf = models.ForeignKey(Conference)
    def __str__(self):
        return self.s_name

class User(models.Model):
    username = models.CharField(max_length=32, primary_key=True) 
    name = models.CharField(max_length=32)
    phone = models.CharField(max_length=32, blank=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(max_length=256)
    #avatar = models.ImageField()
    company = models.CharField(max_length=256, blank=True)
    position = models.CharField(max_length=256, blank=True)
    web = models.URLField(max_length=512, blank=True)
    facebook = models.URLField(max_length=512, blank=True)
    twitter = models.URLField(max_length=512, blank=True)
    google = models.URLField(max_length=512, blank=True)
    linkedin = models.URLField(max_length=512, blank=True)
    bio = models.TextField (blank=True)
    def __str__(self):
        return self.username
    def is_Speaker(self):
        return Event.objects.filter(speaker=self.username) != [] 
    def is_Reviewer(self):
        return Paper.objects.filter(reviewer=self.username) != [] 
    

class EventType(models.Model):
    type_name = models.CharField(max_length=256)
    def __str__(self):
        return self.type_name

class Event(models.Model):
    conf = models.ForeignKey(Conference)
    e_type = models.ForeignKey(EventType)
    event_start = models.DateTimeField(blank=True, null=True)
    event_end = models.DateTimeField(blank=True, null=True)
    room = models.ForeignKey(Room, blank=True, null=True)
    topic = models.CharField(max_length=256)
    description = models.TextField()
    lang = models.CharField(max_length=6)
    slide_url = models.URLField(max_length=512)
    video_url = models.URLField(max_length=512, blank=True)
    event_url = models.URLField(max_length=512)
    speaker = models.ManyToManyField(User, related_name='usr+')
    volunteer = models.ManyToManyField(User, related_name='vol+', blank=True)
    def __str__(self):
        return self.topic
    def is_Scheduled(self):
        return (self.event_start != None) and (self.event_end != None) 

class Paper(models.Model):
    user = models.ForeignKey(User)
    title = models.CharField(max_length=256)
    abstract = models.TextField()
    #source = models.FileField()
    accept = models.NullBooleanField()
    reviewer = models.ManyToManyField(User, related_name='rev+')
    def __str__(self):
        return self.title
