from datetime import datetime, timedelta, date

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from confla.utils import user_rename_and_return_path, paper_rename_and_return_path
from confla.utils import icon_rename_and_return_path, splash_rename_and_return_path

class Conference(models.Model):
    name = models.CharField(max_length=256)
    url_id = models.CharField(max_length=256, unique=True)
    timezone = models.CharField(max_length=256, blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    cfp_start = models.DateField(blank=True, null=True)
    cfp_end = models.DateField(blank=True, null=True)
    rooms = models.ManyToManyField('Room', through='HasRoom', related_name='room+', blank=True)
    timedelta = models.IntegerField(default=10)
    active = models.BooleanField(default=False)
    about = models.TextField(blank=True)
    venue = models.TextField(blank=True)
    gps = models.CharField(max_length=256, blank=True)
    splash = models.ImageField(upload_to=splash_rename_and_return_path,
                                blank=True, null=True)
    icon = models.ImageField(upload_to=icon_rename_and_return_path,
                                blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def cfp_open(self):
        return (self.cfp_start and self.cfp_end and
            self.cfp_start <= datetime.now().date() <= self.cfp_end)

    def has_datetimes(self):
        return (self.start_time and self.end_time and self.start_date and self.end_date)

    # Returns a list of times during a day for a defined timedelta
    def get_delta_list(self):
        def delta_func(start, end, delta):
            current = start
            while current < end:
                yield current
                current = (datetime.combine(date.today(), current) + delta).time()

        if self.has_datetimes():
            mins = self.timedelta
            delta_list = [x.strftime("%H:%M") for x in delta_func(self.start_time,
                                                                    self.end_time,
                                                                    timedelta(minutes=mins))]
        else:
            delta_list = []

        return delta_list

    # Returns a list of datetimes during a day for a defined timedelta
    def get_datetime_time_list(self):
        def delta_func(start, end, delta):
            current = start
            while current < end:
                yield current
                current = (datetime.combine(date.today(), current) + delta).time()

        if self.has_datetimes():
            tz = timezone.get_default_timezone()
            offset = tz.utcoffset(datetime.now())
            tz_start = datetime.combine(self.start_date, self.start_time)
            tz_end = datetime.combine(self.end_date, self.end_time)
            tz_start = tz_start + offset
            tz_end = tz_end + offset
            mins = self.timedelta
            delta_list = [x for x in delta_func(tz_start.time(),
                                                    tz_end.time(),
                                                    timedelta(minutes=mins))]
        else:
            delta_list = []

        return delta_list

    # Returns a list of days formated as a string
    def get_date_list(self):
        if self.has_datetimes():
            day_num = (self.end_date - self.start_date).days + 1
            date_list = [(self.start_date + timedelta(days=x)).strftime("%A, %d.%m.")
                            for x in range(0, day_num)]
        else:
            date_list = []
        return date_list

    # Returns a list of days as a datetime
    def get_datetime_date_list(self):
        if self.has_datetimes():
            day_num = (self.end_date - self.start_date).days + 1
            date_list = [(self.start_date + timedelta(days=x))
                            for x in range(0, day_num)]
        else:
            date_list = []
        return date_list

    @property
    def get_unscheduled_events(self):
        return Event.objects.filter(conf_id=self, timeslot__isnull=True)

    @property
    def get_scheduled_events(self):
        return Event.objects.filter(conf_id=self, timeslot__isnull=False)

    @property
    def get_speakers(self):
        return ConflaUser.objects.filter(events__conf_id=self, events__timeslot__isnull=False).distinct()

    @property
    def get_tags(self):
        return EventTag.objects.filter(event__conf_id=self, event__timeslot__isnull=False).distinct()

class Room(models.Model):
    shortname = models.CharField(max_length=16)
    name = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=8, blank=True)

    def __str__(self):
        return self.shortname

class HasRoom(models.Model):
    room = models.ForeignKey(Room)
    conference = models.ForeignKey(Conference)
    slot_length = models.IntegerField(default=10)
    order = models.IntegerField(null=True)

class ConflaUser(AbstractUser):
    phone = models.CharField(max_length=32, blank=True)
    picture = models.ImageField(upload_to=user_rename_and_return_path,
                                blank=True, null=True)
    company = models.CharField(max_length=256, blank=True)
    position = models.CharField(max_length=256, blank=True)
    web = models.URLField(max_length=512, blank=True)
    github = models.URLField(max_length=512, blank=True)
    facebook = models.URLField(max_length=512, blank=True)
    twitter = models.URLField(max_length=512, blank=True)
    google_plus = models.URLField(max_length=512, blank=True)
    linkedin = models.URLField(max_length=512, blank=True)
    bio = models.TextField (blank=True)
    schedule = models.ManyToManyField('Event', related_name='sched+', blank=True)

    def __str__(self):
        return self.username

    def is_Speaker(self):
        return len(Event.objects.filter(speaker=self.username)) != 0

    def is_Reviewer(self):
        return len(Paper.objects.filter(reviewer=self.username)) != 0

    @property
    def get_fullname(self):
        return (self.first_name + ' ' + self.last_name).strip()

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
    color = models.CharField(max_length=8, blank=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    conf_id = models.ForeignKey(Conference)
    topic = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    lang = models.CharField(max_length=6)
    slides = models.URLField(max_length=512, blank=True)
    video = models.URLField(max_length=512, blank=True)
    google_doc_url = models.URLField(max_length=512, blank=True)
    speaker = models.ManyToManyField(ConflaUser, blank=True, related_name='events')
    tags = models.ManyToManyField(EventTag, related_name='events', blank=True)
    prim_tag = models.ForeignKey(EventTag, null=True, blank=True)
    notes = models.TextField(blank=True)
    reqs = models.TextField(blank=True)

    def __str__(self):
        return self.topic

    @property
    def is_scheduled(self):
        try:
            if hasattr(self, 'timeslot'):
                return True
        except ObjectDoesNotExist:
            return False

class Timeslot(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    room_id = models.ForeignKey(Room, blank=True, null=True)
    event_id = models.OneToOneField(Event, blank=True, null=True)
    conf_id = models.ForeignKey(Conference)

    @property
    def get_start_time(self):
        return self.start_time.astimezone(timezone.get_default_timezone()).time().strftime("%H:%M")

    @property
    def get_start_datetime(self):
        return self.start_time.astimezone(timezone.get_default_timezone())

    @property
    def get_end_time(self):
        return self.end_time.astimezone(timezone.get_default_timezone()).time().strftime("%H:%M")

    @property
    def get_end_datetime(self):
        return self.end_time.astimezone(timezone.get_default_timezone()).strftime("%x %H:%M")

    # event length in minutes
    @property
    def length(self):
        if self.start_time and self.end_time:
            return ((self.end_time - self.start_time).seconds / 60) / self.conf_id.timedelta

class Paper(models.Model):
    conf_id = models.ForeignKey(Conference)
    user = models.ForeignKey(ConflaUser)
    title = models.CharField(max_length=256)
    abstract = models.TextField()
    source = models.FileField(upload_to=paper_rename_and_return_path,
                                blank=True, null=True)
    accepted = models.NullBooleanField()
    reviewer = models.ManyToManyField(ConflaUser, related_name='rev+', blank=True)
    review_notes = models.TextField()

    def __str__(self):
        return self.title

class Photo(models.Model):
    conf_id = models.ForeignKey(Conference)
    author = models.CharField(max_length=256)
    picture = models.ImageField(upload_to='photos/')

class Page(models.Model):
    conf_id = models.ForeignKey(Conference)
    title = models.CharField(max_length=256)
    abstract = models.TextField()
