from django.db import models

class Conf(models.Model):
    name = models.CharField(max_length=256)

class Room(models.Model):
    s_name = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    desc = models.TextField()
    color = models.CharField(max_length=8)
    conf = models.ForeignKey(Conf)

class User(models.Model):
    username = models.CharField(max_length=32, primary_key=True) 
    name = models.CharField(max_length=32)
    phone = models.CharField(max_length=32)
    sha1 = models.CharField(max_length=256)
    email = models.EmailField(max_length=256)
    #avatar = models.ImageField()
    company = models.CharField(max_length=256)
    position = models.CharField(max_length=256)
    web = models.URLField(max_length=512)
    facebook = models.URLField(max_length=512)
    twitter = models.URLField(max_length=512)
    google = models.URLField(max_length=512)
    linkedin = models.URLField(max_length=512)
    bio = models.TextField()

class EventType(models.Model):
    type_name = models.CharField(max_length=256)

class Event(models.Model):
    conf = models.ForeignKey(Conf)
    e_type = models.ForeignKey(EventType)
    event_start = models.DateTimeField()
    event_end = models.DateTimeField()
    room = models.ForeignKey(Room)
    topic = models.CharField(max_length=256)
    desc = models.TextField()
    lang = models.CharField(max_length=6)
    slide_url = models.URLField(max_length=512)
    video_url = models.URLField(max_length=512)
    event_url = models.URLField(max_length=512)
    speaker = models.ManyToManyField(User)
