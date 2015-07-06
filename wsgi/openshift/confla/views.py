from datetime import datetime
import json
import random

from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.utils import timezone

from confla.models import *
from confla.forms import *

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class VolunteerView(generic.TemplateView):
    template_name = 'confla/volunteer.html'

    @permission_required('confla.can_volunteer', raise_exception=True)
    def my_view(request):
        return render(request, VolunteerView.template_name)

class ScheduleView(generic.TemplateView):
    template_name = 'confla/usertable.html'

    def my_view(request):
        #TODO: Add compatibility with archived conferences
        conf = Conference.get_active()
        slot_list = {}
        rooms = conf.rooms.all()
        for room in rooms:
            slot_list[room.shortname] = Timeslot.objects.filter(conf_id=conf, room_id=room).order_by("start_time")
        if not(conf):
            return HttpResponse("Currently no conferences.")
        time_list = []
        start_list = conf.get_datetime_time_list()
        for date in conf.get_datetime_date_list():
            time_dict = {}
            time_dict["day"] = date.strftime("%A, %d.%m.")
            time_dict["list"] = []
            for start_time in start_list:
                time = {}
                time['short'] = start_time.strftime("%H:%M") 
                time['full'] = datetime.combine(date, start_time).strftime("%x %H:%M") 
                time['slots'] = []
                for room in rooms:
                    for slot in slot_list[room.shortname]:
                        if slot.get_start_datetime == time['full']:
                            time['slots'].append(slot)
                            break
                    else:
                        time['slots'].append(None)
                time_dict["list"].append(time)
            time_list.append(time_dict)

        return render(request, ScheduleView.template_name,
                    {    'time_list' : time_list,
                         'tag_list' : EventTag.objects.all(),
                         'room_list' : [{'conf' : conf,
                                         'room' : x} for x in rooms],
                    })

    def list_view(request):
        #TODO: Add compatibility with archived conferences
        conf = Conference.get_active()
        if not(conf):
            return HttpResponse("Currently no conferences.")
        time_list = []
        # Distinct ordered datetime list for the current conference
        start_list = Timeslot.objects.filter(conf_id=conf).order_by("start_time").values_list("start_time", flat=True).distinct()
        slot_list = Timeslot.objects.filter(conf_id=conf)
        for date in conf.get_date_list():
            time_dict = {}
            time_dict["day"] = date
            time_dict["list"] = []
            for start_time in start_list:
                if start_time.strftime("%A, %d.%m.") == date:
                    time = {}
                    time['short'] = start_time.strftime("%H:%M") 
                    time['full'] = start_time.strftime("%x %H:%M") 
                    time['slots'] = []
                    for slot in slot_list:
                        if slot.get_start_datetime == time['full']:
                            time['slots'].append(slot)
                    time_dict["list"].append(time)
            time_list.append(time_dict)

        return render(request, "confla/schedlist.html",
                      {  'time_list' : time_list, 
                         'tag_list' : EventTag.objects.all(),
                         'room_list' : [{'conf' : conf,
                                         'room' : x} for x in conf.rooms.all()],
                    })

class LoginView(generic.TemplateView):
    template_name = 'confla/login.html'

    def my_view(request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('confla:users'))
        else:
            return render(request, 'confla/login.html', {
            'form' : AuthForm(),
        })

    #TODO: OpenSSL,  or some other crypto for POST
    def auth_and_login(request):
        if not(request.method == "POST"):
            return HttpResponseRedirect(reverse('confla:login'))

        if request.POST['next'] is not "":
            redirect = request.POST['next']
        else:
            redirect = reverse('confla:users')

        try:
            user = authenticate(username=request.POST['username'],
                                password=request.POST['password'])
            if user:
                if user.is_active:
                    login(request, user)
                else:
                    #disabled account
                    return render(request, 'confla/login.html', {
                                    'error_message': _("Your account is disabled."),
                                    'form' : AuthForm()})
            else:
                #invalid login
                raise ConflaUser.DoesNotExist

        except (KeyError, ConflaUser.DoesNotExist):
            return render(request, 'confla/login.html', {
                         'error_message': _("Wrong username/password."),
                         'form' : AuthForm()})

        else:
            # all is OK, redirect the logged in user to the user site
            return HttpResponseRedirect(redirect)

    def logout(request):
        logout(request)
        return HttpResponseRedirect(reverse('confla:login'))

class UserView(generic.TemplateView):
    template_name = 'confla/base.html'

    @login_required
    def my_view(request):
        return render(request, UserView.template_name)

    @login_required
    def add_email(request):
        if request.method == 'POST':
            form = EmailForm(request.POST)
            user = request.user
            email = EmailAdress()
            email.user = user
            email.address = request.POST['address']
            try:
                email.full_clean()
            except ValidationError:
                user_form = ProfileForm(instance=request.user)
                return render(request, 'confla/profile.html', {
                     'email_form' : form,
                     'email_list' : EmailAdress.objects.filter(user=request.user),
                     'form' : user_form,
                    })
            else:
                email.save()
            return HttpResponseRedirect(reverse('confla:profile'))
        else:
            return HttpResponseRedirect(reverse('confla:profile'))

    @login_required
    def delete_email(request):
        if request.method == 'POST' and 'id' in request.POST:
            email = EmailAdress.objects.get(id=request.POST['id'])
            if email.is_primary:
                return render(request, 'confla/profile.html',{
                            'form' : ProfileForm(instance=request.user),
                            'email_list' : EmailAdress.objects.filter(user=request.user),
                            'email_form' : EmailForm(),
                            'error_message' : _("Cannot remove primary email."),
                })
            else:
                email.delete()
            return HttpResponseRedirect(reverse('confla:profile'))
        else:
            return HttpResponseRedirect(reverse('confla:profile'))

    @login_required
    def view_profile(request):
        if request.method == 'POST':
            form = ProfileForm(data=request.POST, instance=request.user)
            if form.is_valid():
                user = form.save(commit=False)
                user.save()
                # TODO: make own "Your changes have been saved." page
                return HttpResponseRedirect(reverse('confla:thanks'))
        else:
                form = ProfileForm(instance=request.user)
                email_form = EmailForm()

        return render(request, 'confla/profile.html',{
            'form' : form,
            'email_list' : EmailAdress.objects.filter(user=request.user),
            'email_form' : email_form,
            })

    @login_required
    def send_paper(request):
        if request.method == 'POST':
            paper_form = PaperForm(request.POST)
            if paper_form.is_valid():
                paper = paper_form.save(commit=False)
                paper.user_id = request.user.id
                paper.save()
                return HttpResponseRedirect(reverse('confla:thanks'))
        else:
            paper_form = PaperForm()

        return render(request, 'confla/reg_talk.html', {
            'paper_form': paper_form,
        })

class RegisterView(generic.TemplateView):
    template_name = 'confla/thanks.html'

    def user_register(request):
        if request.method == 'POST': # the form was submitted
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save()
                email = EmailAdress()
                email.user = user
                email.address = user.email
                try:
                    email.full_clean()
                except ValidationError as e:
                    user.delete()
                    errors = []
                    for key in e.args[0]:
                        errors += e.args[0][key]
                    form.errors['__all__'] = form.error_class(errors)
                    return render(request, 'confla/register.html', {
                         'form' : form})
                else:
                    email.save()

                return HttpResponseRedirect(reverse('confla:thanks'))
        else:
            form = RegisterForm()

        return render(request, 'confla/register.html', {
            'form' : form,
        })

    def send_paper(request):
        if request.method == 'POST':
            user_form = RegisterForm(request.POST)
            paper_form = PaperForm(request.POST)
            if user_form.is_valid() and paper_form.is_valid():
                user = user_form.save()
                paper = paper_form.save(commit=False)
                paper.user_id = user.id;
                paper.save()
                return HttpResponseRedirect(reverse('confla:thanks'))
        else:
            user_form = RegisterForm()
            paper_form = PaperForm()

        return render(request, 'confla/reg_talk.html', {
            'user_form': user_form,
            'paper_form': paper_form,
        })

class AddRoomsView(generic.TemplateView):
    template_name="confla/add_rooms.html"

    @permission_required('confla.can_organize', raise_exception=True)
    def view_form(request):
        if request.method == 'POST':
            form = RoomCreateForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponse(render_to_string('confla/add_rooms_success.html'))
        else:
            form = RoomCreateForm()

        return render(request, 'confla/add_rooms.html', {
            'rooms_form' : form,
        })

class TimetableView(generic.TemplateView):
    template_name = "confla/timetable.html"

    def view_timetable(request):
        #TODO: Check if organizer before creating a conf form
        if len(Conference.objects.all()) == 0:
            if request.method == 'POST': # the form was submitted
                form = ConfCreateForm(request.POST)
                if form.is_valid():
                    conf = form.save(commit=False)
                    conf.active = True
                    conf.save()
                    form.save_m2m()
                    return HttpResponseRedirect(reverse('confla:thanks'))
            else:
                form = ConfCreateForm()

            return render(request, 'confla/newconf.html', {
                'form' : form,
            })
        else:
            #TODO: Add compatibility with archived conferences
            conf = Conference.get_active()
            if not(conf):
                return HttpResponse("Currently no conferences.")
            users = ConflaUser.objects.all()
            tags = EventTag.objects.all()
            rooms = conf.rooms.all()
            slot_list = {}
            for room in rooms:
                slot_list[room.shortname] = Timeslot.objects.filter(conf_id=conf, room_id=room).order_by("start_time")
            time_list = []
            start_list = conf.get_datetime_time_list()
            for date in conf.get_datetime_date_list():
                time_dict = {}
                time_dict["day"] = date.strftime("%A, %d.%m.")
                time_dict["list"] = []
                for start_time in start_list:
                    time = {}
                    time['short'] = start_time.strftime("%H:%M") 
                    time['full'] = datetime.combine(date, start_time).strftime("%x %H:%M") 
                    time['slots'] = []
                    for room in rooms:
                        for slot in slot_list[room.shortname]:
                            if slot.get_start_datetime == time['full']:
                                time['slots'].append(slot)
                                break
                        else:
                            time['slots'].append(None)
                    time_dict["list"].append(time)
                time_list.append(time_dict)

            return render(request, TimetableView.template_name,
                          {  'conf'      : conf,
                             'event_create' : EventCreateForm(),
                             'tag_list' : [{'id' : x.id,
                                            'color' : x.color}
                                            for x in EventTag.objects.all()],
                             'event_list' : Event.objects.filter(timeslot__isnull=True).filter(conf_id=conf),
                             'time_list' : time_list,
                             'room_list' : [{'conf' : conf,
                                             'room' : x} for x in conf.rooms.all()],
                             'user_list' : [{'name' : u.first_name + ' ' + u.last_name,
                                             'username' : u.username} for u in users],
                           })

    @permission_required('confla.can_organize', raise_exception=True)
    def save_timetable(request):
        if(request.method == 'POST'):
            TimetableView.json_to_timeslots(request.POST['data'])
            return HttpResponseRedirect(reverse('confla:thanks'))

    def save_event(request):
        if request.method == 'POST':
            if request.POST['event_id'] == "0":
                form = EventCreateForm(request.POST)
                if form.is_valid():
                    new_event = form.save(commit=False)
                    new_event.conf_id = Conference.get_active()
                    new_event.e_type_id = EventType.objects.get(id=1)
                    new_event.lang = "cz"
                    if "tags" in request.POST:
                        new_event.prim_tag = EventTag(id=request.POST.getlist('tags')[0])
                    new_event.save()
                    form.save_m2m()
                    return HttpResponse(new_event.id)
                else:
                    return HttpResponse("-1")
            else:
                event = Event.objects.get(id=request.POST['event_id'])
                form = EventCreateForm(data=request.POST, instance=event)
                if form.is_valid():
                    event = form.save(commit=False)
                    if "tags" in request.POST:
                        event.prim_tag = EventTag(id=request.POST.getlist('tags')[0])
                    else:
                        event.prim_tag = None
                    event.save()
                    form.save_m2m()
                else:
                    print("invalid")
                return HttpResponseRedirect(reverse('confla:thanks'))

    def json_to_timeslots(json_string):
        # JSON format: '[{"Room" : {"start" : "HH:MM", "end" : "HH:MM"}}]'
        conf = Conference.get_active()
        json_obj = json.loads(json_string)
        ids = []
        # Create new timeslots from JSON
        for row in json_obj:
            # row: one row in the timeslot table
            # key: room shortname, also dictionary key for timeslots
            for key in row:
                # Check if its a new slot or an edited existing one
                if row[key]['id'] == '0':
                    newslot = Timeslot()
                else:
                    newslot = Timeslot.objects.get(id=int(row[key]['id']))
                # If the slot has an event bound to it
                if row[key]['event'] != "0":
                    newslot.event_id = Event.objects.get(id=row[key]['event'])
                else:
                    newslot.event_id = None
                newslot.room_id = Room.objects.get(shortname=key)
                newslot.conf_id = conf
                # Has to be like this or else django complains!
                start = datetime.strptime(row[key]['start'], "%H:%M")
                end = datetime.strptime(row[key]['end'], "%H:%M")
                date = datetime.strptime(row[key]['day'], "%A, %d.%m.")
                year = conf.start_date.year
                newslot.start_time = timezone.now().replace(year=year, month=date.month,
                                                        day=date.day, hour=start.hour, minute=start.minute,
                                                        second=0, microsecond=0)
                newslot.end_time = timezone.now().replace(year=year, month=date.month,
                                                        day=date.day, hour=end.hour, minute=end.minute,
                                                        second=0, microsecond=0)
                # Add slot to db
                try:
                    newslot.full_clean()
                except ValidationError as e:
                    if ('event_id' in e.error_dict and
                            e.error_dict['event_id'][0] == 'Timeslot with this Event id already exists.'):
                        oldslot = Timeslot.objects.get(event_id=newslot.event_id)
                        oldslot.event_id = None
                        oldslot.save()
                        newslot.full_clean()
                    else:
                        raise e
                newslot.save()
                ids.append(newslot.id)

        print(ids)
        Timeslot.objects.exclude(id__in=ids).delete()

class ImportView(generic.TemplateView):
    template_name = "confla/import.html"

    json_s = """{ "rooms" : [{
                        "id" : 100,
                        "s_name" : "r2",
                        "name" : "",
                        "desc" : "",
                        "color" : ""
                    }],
                "confs" : [{
                        "id" : 100,
                        "name" : "JSON_conf",
                        "rooms" : [100],
                        "start_t" : "10:00",
                        "end_t" : "18:00",
                        "start_d" : "27/03/2016",
                        "end_d" : "28/03/2016",
                        "time_d" : 10,
                        "active" : true
                    }],
                "slots" : [{
                        "id" : 1,
                        "conf_id" : 100,
                        "room_id" : 100,
                        "start_t" : "10:10",
                        "end_t" : "10:50"
                    },
                    {
                        "id" : 2,
                        "conf_id" : 100,
                        "room_id" : 100,
                        "start_t" : "12:10",
                        "end_t" : "12:50"
                    }],
                "users" : [{
                        "username" : "testor",
                        "f_name" : "First name",
                        "l_name" : "Last name",
                        "password" : "pbkdf2_sha256$12000$tM9lc9JIW9ZE$Yl8pbU25d3y5xEnUv7WqoPU1Kduo/7C4xps5SR/+fEM=",
                        "phone" : "",
                        "company" : "",
                        "position" : "",
                        "web" : "",
                        "github" : "",
                        "facebook" : "",
                        "twitter" : "",
                        "g+" : "",
                        "linkedin" : "",
                        "bio" : ""
                    }],
                "e_types" : [{
                         "id" : 1,
                         "name" : "talk"
                    }],
                "events" : [{
                         "id" : 1,
                         "type_id" : 1,
                         "conf_id" : 100,
                         "topic" : "topic",
                         "desc" : "description",
                         "lang" : "Czech",
                         "slides" : "",
                         "video" : "",
                         "g_doc" : "",
                         "speakers" : ["testor"]
                    }]
            }"""

    def json_to_db(json_string):
        json_obj = json.loads(json_string)

        # Generate rooms
        room_list = json_obj['rooms']
        for room in room_list:
            newroom = Room()
            newroom.id = room['id']
            newroom.shortname = room['s_name']
            newroom.name = room['name']
            newroom.description = room['desc']
            newroom.color = room['color']
            try:
                newroom.full_clean()
            except ValidationError as e:
                if ('id' in e.error_dict and
                        e.error_dict['id'][0] == 'Room with this ID already exists.'):
                    Room.objects.get(id=newroom.id).delete()
                    newroom.full_clean()
                else:
                    raise e
            newroom.save()

        # Generate conferences
        conf_list = json_obj['confs']
        for conf in conf_list:
            newconf = Conference()
            newconf.id = conf['id']
            newconf.name = conf['name']
            # Has to be like this or else django complains!
            start = datetime.strptime(conf['start_t'], "%H:%M")
            end = datetime.strptime(conf['end_t'], "%H:%M")
            newconf.start_time = timezone.now().replace(hour=start.hour, minute=start.minute,
                                                            second=0, microsecond=0)
            newconf.end_time = timezone.now().replace(hour=end.hour, minute=end.minute,
                                                            second=0, microsecond=0)
            newconf.start_date = datetime.strptime(conf['start_d'], "%d/%m/%Y")
            newconf.end_date = datetime.strptime(conf['end_d'], "%d/%m/%Y")
            newconf.timedelta = conf['time_d']
            newconf.active = conf['active']
            # Conference has to be in db before we can add rooms
            try:
                newconf.full_clean()
            except ValidationError as e:
                if ('id' in e.error_dict and
                        e.error_dict['id'][0] == 'Conference with this ID already exists.'):
                    Conference.objects.get(id=newconf.id).delete()
                    newconf.full_clean()
                else:
                    raise e

            newconf.save()

            for room in conf['rooms']:
                newconf.rooms.add(Room.objects.get(id=room))
            newconf.save()

        # Generate timeslots
        slot_list = json_obj['slots']
        for slot in slot_list:
            newslot = Timeslot()
            newslot.id = slot['id']
            newslot.conf_id = Conference.objects.get(id=slot['conf_id'])
            newslot.room_id = Room.objects.get(id=slot['room_id'])
            # Has to be like this or else django complains!
            start = datetime.strptime(slot['start_t'], "%H:%M")
            end = datetime.strptime(slot['end_t'], "%H:%M")
            newslot.start_time = timezone.now().replace(hour=start.hour, minute=start.minute,
                                                        second=0, microsecond=0)
            newslot.end_time = timezone.now().replace(hour=end.hour, minute=end.minute,
                                                        second=0, microsecond=0)
            try:
                newslot.full_clean()
            except ValidationError as e:
                if ('id' in e.error_dict and
                        e.error_dict['id'][0] == 'Timeslot with this ID already exists.'):
                    Timeslot.objects.get(id=newslot.id).delete()
                    newslot.full_clean()
                else:
                    raise e
            newslot.save()

        # Generate users
        user_list = json_obj['users']
        for user in user_list:
            newuser = ConflaUser()
            newuser.username = user['username']
            newuser.password = user['password']
            newuser.first_name = user['f_name']
            newuser.last_name = user['l_name']
            newuser.phone = user['phone']
            newuser.picture = None
            newuser.company = user['company']
            newuser.position = user['position']
            newuser.web = user['web']
            newuser.github = user['github']
            newuser.facebook = user['facebook']
            newuser.twitter = user['twitter']
            newuser.google_plus = user['g+']
            newuser.linkedin = user['linkedin']
            newuser.bio = user['bio']
            try:
                newuser.full_clean()
            except ValidationError as e:
                if ('username' in e.error_dict and
                        e.error_dict['username'][0] == 'Confla user with this Username already exists.'):
                    ConflaUser.objects.get(username=newuser.username).delete()
                    newuser.full_clean()
                else:
                    raise e
            newuser.save()

        # Generate event types
        event_type_list = json_obj['e_types']
        for etype in event_type_list:
            newtype = EventType()
            newtype.id = etype['id']
            newtype.name = etype['name']
            try:
                newtype.full_clean()
            except ValidationError as e:
                if ('id' in e.error_dict and
                        e.error_dict['id'][0] == 'Event type with this ID already exists.'):
                    EventType.objects.get(id=newtype.id).delete()
                    newtype.full_clean()
                else:
                    raise e
            newtype.save()

        # Generate events
        event_list = json_obj['events']
        for event in event_list:
            newevent = Event()
            newevent.id = event['id']
            newevent.conf_id = Conference.objects.get(id=event['conf_id'])
            newevent.e_type_id = EventType.objects.get(id=event['type_id'])
            newevent.topic = event['topic']
            newevent.description = event['desc']
            newevent.lang = event['lang']
            newevent.slides = event['slides']
            newevent.video = event['video']
            newevent.google_doc_url = event['g_doc']
            try:
                newevent.full_clean()
            except ValidationError as e:
                if ('id' in e.error_dict and
                        e.error_dict['id'][0] == 'Event with this ID already exists.'):
                    Event.objects.get(id=newevent.id).delete()
                    newevent.full_clean()
                else:
                    raise e
            newevent.save()
            for speaker in event['speakers']:
                newevent.speaker.add(ConflaUser.objects.get(username=speaker))
            newevent.save()

    # import json from devconf for testing purposes
    def dv(json_string):
        # delete everyone excluding admin
        ConflaUser.objects.all().exclude(username="admin").delete()
        json_obj = json.loads(json_string)

        Timeslot.objects.all().delete()
        Event.objects.all().delete()
        EventTag.objects.all().delete()
        room_list = []
        for i in Room.objects.all():
            room_list.append(i.shortname)
        user_list = []
        tag_list = []

        # Generate sessions
        event_list = json_obj['sessions']
        for event in event_list:
            newevent = Event()
            newevent.conf_id = Conference.get_active()
            newevent.e_type_id = EventType.objects.get(id=1)
            newevent.topic = event['topic']
            newevent.description = event['description']
            newevent.lang = event['lang']

            newevent.full_clean()
            newevent.save()

            # Create timeslot for the event
            newslot = Timeslot()
            newslot.conf_id = Conference.get_active()
            if event['room'] in room_list:
                newslot.room_id = Room.objects.get(shortname=event['room'])
            # Has to be like this or else django complains!
            start = datetime.fromtimestamp(int(event['event_start']))
            end = datetime.fromtimestamp(int(event['event_end']))
            newslot.start_time = timezone.now().replace(year=start.year, month=start.month,
                                                        day=start.day, hour=start.hour, minute=start.minute,
                                                        second=0, microsecond=0)
            newslot.end_time = timezone.now().replace(year=end.year, month=end.month,
                                                        day=end.day, hour=end.hour, minute=end.minute,
                                                        second=0, microsecond=0)
            newslot.event_id = newevent
            #if (start.day == 6):
            newslot.full_clean()
            newslot.save()

            # Create speakers
            for speaker in event['speakers']:
                username = speaker.replace(" ", "")[:30]
                if username in user_list:
                    newevent.speaker.add(ConflaUser.objects.get(username=username))
                else:
                    newuser = ConflaUser()
                    newuser.username = username
                    newuser.password = "blank"
                    newuser.first_name = speaker
                    try:
                        newuser.full_clean()
                    except ValidationError as e:
                        pass
                    newuser.save()
                    newevent.speaker.add(newuser)
                    user_list.append(username)
            if event['tags']:
                tags = event['tags'][0].split(",")
            else:
                tags = ['notag']
            # Create tags
            for tag in tags:
                tag = tag.strip()
                if tag in tag_list:
                    newevent.tags.add(EventTag.objects.get(name=tag))
                else:
                    newtag = EventTag()
                    newtag.name = tag
                    newtag.color = "#%06x" % random.randint(0,0xFFFFFF)
                    try:
                        newtag.full_clean()
                    except ValidationError as e:
                        pass
                    newtag.save()
                    newevent.tags.add(newtag)
                    tag_list.append(tag)

            newevent.prim_tag = EventTag.objects.get(name=tags[0])
            newevent.save()   

        """
        # Generate users
        user_list = json_obj['users']
        for user in user_list:
            newuser = ConflaUser()
            newuser.username = user['username']
            newuser.password = "blank"
            if 'name' in user:
                newuser.first_name = user['name']
            try:
                newuser.full_clean()
            except ValidationError as e:
                pass

            newuser.save()
        """
