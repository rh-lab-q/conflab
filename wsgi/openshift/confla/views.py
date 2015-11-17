import json
import random
import re
import hashlib
import csv
import io
from datetime import datetime, date, time

from django.template.loader import render_to_string
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.db import transaction

from confla.forms import *
from confla.models import *
from confla.view_utils import get_conf_or_404

class TestingView(generic.TemplateView):
    @permission_required('confla.can_organize', raise_exception=True)
    def test(request, url_id):
        return ExportView.csv(request, url_id)

class AdminView(generic.TemplateView):

    @permission_required('confla.can_organize', raise_exception=True)
    def dashboard(request, url_id=None):
        if url_id:
            conf = get_conf_or_404(url_id)
        return render(request, "confla/admin/admin_base.html",
                        {   'url_id' : url_id,
                        })

    @permission_required('confla.can_organize', raise_exception=True)
    def schedule(request, url_id):
        conf = get_conf_or_404(url_id)

        slot_list = {}
        rooms = conf.rooms.all()
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

        return render(request, "confla/admin/user_sched.html",
                    {    'time_list' : time_list,
                         'tag_list' : EventTag.objects.all(),
                         'room_list' : [{'conf' : conf,
                                         'room' : x} for x in rooms],
                         'url_id' : url_id,
                    })

class EventEditView(generic.TemplateView):
    template_name = 'confla/event_edit.html'

    @permission_required('confla.can_organize', raise_exception=True)
    def event_view(request, url_id, id=None):
        conf = get_conf_or_404(url_id)

        event = None
        if id:
            event = Event.objects.get(id=id)
        event_list = Event.objects.filter(conf_id=conf)
        users = ConflaUser.objects.all()
        tags = EventTag.objects.all()
        return render(request, EventEditView.template_name,
                        { 'event_list' : event_list, 
                          'tag_list' : EventTag.objects.all(),
                          'event': event,
                          'user_list' : [{ 'name' : u.first_name + ' ' + u.last_name,
                                           'username' : u.username,
                                           'id' : u.id } for u in users],
                          })

    @permission_required('confla.can_organize', raise_exception=True)
    def event_save(request, url_id, id):
        if request.method == 'POST':
            conf = get_conf_or_404(url_id)

            data = request.POST.copy()
            data['conf_id'] = conf
            event = None
            try:
                event = Event.objects.get(id=id)
            except ObjectDoesNotExist:
                raise Http404
            form = EventEditForm(data=data, instance=event)
            if form.is_valid():
                event = form.save(commit=False)
                if "tags" in request.POST:
                    event.prim_tag = EventTag(id=request.POST.getlist('tags')[0])
                else:
                    event.prim_tag = None
                event.save()
                form.save_m2m()
            else:
                #TODO: Proper error handling
                print(form.errors)

            return HttpResponseRedirect(reverse('confla:editEvent', kwargs={'url_id' : url_id}))
        else:
            raise Http404

    @permission_required('confla.can_organize', raise_exception=True)
    def event_modal(request):
        if not(request.method == "POST"):
            raise Http404
        try:
            event = Event.objects.get(id=int(request.POST['data']))
        except ObjectDoesNotExist:
                raise Http404
        return render(request, 'confla/event_modal.html',
                        {   'form' : EventEditForm(instance=event),
                            'event': event,
                        })

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'
    def my_view(request, url_id):
        conf = get_conf_or_404(url_id)
        return render(request, AboutView.template_name, {'url_id' : url_id})

class IndexView(generic.TemplateView):
    template_name = 'confla/index.html'
    def my_view(request):
        conf_list = Conference.objects.all();
        return render(request, IndexView.template_name, {'conf_list' : conf_list})

class CfpView(generic.TemplateView):
    # TODO: Combine these two methods
    # TODO: Conference.objects.get(url_id=url_id) to get conference
    @login_required
    def save_form_and_register(request, url_id):
        conf = get_conf_or_404(url_id)

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
            'url_id' : url_id,
        })

    @login_required
    def save_form(request, url_id):
        conf = get_conf_or_404(url_id)

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

class VolunteerView(generic.TemplateView):
    template_name = 'confla/volunteer.html'

    @permission_required('confla.can_volunteer', raise_exception=True)
    def my_view(request):
        return render(request, VolunteerView.template_name)

class EventView(generic.TemplateView):

    def get_popover(request):
        template_name = 'confla/event_popover.html'
        if not(request.method == "POST"):
            raise Http404
        event = Event.objects.get(id=int(request.POST['data']))
        return render(request, template_name, {'event': event})

    @permission_required('confla.can_organize', raise_exception=True)
    def get_admin_popover(request, url_id):
        template_name = 'confla/event_popover_admin.html'
        conf = get_conf_or_404(url_id)

        if not(request.method == "POST"):
            raise Http404
        event_id = int(request.POST['data'])
        print(event_id)
        if event_id > 0:
            event = Event.objects.get(id=int(request.POST['data']))
            form = EventCreateForm(instance=event)
        else:
            form = EventCreateForm()

        return render(request, template_name,
                        {'event_id': event_id,
                         'form'  : form,
                         'url_id' : url_id,
                        })

class ScheduleView(generic.TemplateView):
    template_name = 'confla/user_sched.html'

    def my_view(request, url_id):
        #TODO: Add compatibility with archived conferences
        conf = get_conf_or_404(url_id)

        slot_list = {}
        rooms = conf.rooms.all()
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

        return render(request, ScheduleView.template_name,
                    {    'time_list' : time_list,
                         'tag_list' : EventTag.objects.all(),
                         'room_list' : [{'conf' : conf,
                                         'room' : x} for x in rooms],
                         'url_id' : url_id,
                    })

    def list_view(request, url_id):
        conf = get_conf_or_404(url_id)

        time_list = []
        # Distinct ordered datetime list for the current conference
        start_list = Timeslot.objects.filter(conf_id=conf).order_by("start_time").values_list("start_time", flat=True).distinct()
        slot_list = Timeslot.objects.filter(conf_id=conf)
        for date in conf.get_date_list():
            time_dict = {}
            time_dict["day"] = date
            time_dict["list"] = []
            for start_time in start_list:
                start_time = start_time.astimezone(timezone.get_default_timezone())
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

class RoomConfView(generic.TemplateView):
    template_name = 'confla/slot_edit.html'

    @permission_required('confla.can_organize', raise_exception=True)
    def slot_view(request, url_id):
        conf = get_conf_or_404(url_id)

        rooms = conf.rooms.all()
        room_list = [{'slot_len' : x.hasroom_set.get(conference=conf).slot_length,
                      'room' : x} for x in conf.rooms.all()]
        len_dict = {}
        for config in room_list:
            slot_len = int(config['slot_len'])*conf.timedelta
            try:
                len_dict[slot_len].append(config['room'])
            except KeyError:
                len_dict[slot_len]=[config['room']]
        config_list = []
        for key, value in len_dict.items():
            config_list.append({'slot_len' : key, 'rooms' : value})
        return render(request, RoomConfView.template_name, { 'rooms' : rooms,
                                                'config_list' : config_list,
                                                'url_id' : url_id
                                                })

    @transaction.atomic
    @permission_required('confla.can_organize', raise_exception=True)
    def save_config(request, url_id):
        conf = get_conf_or_404(url_id)

        if request.method == 'POST': # the form was submitted
            configs = json.loads(request.POST['data'])
            for config in configs:
                length = int(int(config['length']) / conf.timedelta)
                # Get HasRoom objects for given Conference and Rooms
                room_confs = HasRoom.objects.filter(room__shortname__in=config['rooms'],
                                                    conference=conf)
                for room_conf in room_confs:
                    room_conf.slot_length = length
                    room_conf.save()
            return HttpResponse(0)

class TimetableView(generic.TemplateView):
    template_name = "confla/admin/edit_sched.html"

    @permission_required('confla.can_organize', raise_exception=True)
    def view_timetable(request, url_id):
        conf = get_conf_or_404(url_id)

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
        room_list = [{'slot_len' : x.hasroom_set.get(conference=conf).slot_length,
                      'room' : x} for x in conf.rooms.all()]
        return render(request, TimetableView.template_name,
                      {  'conf'      : conf,
                         'event_create' : EventCreateForm(),
                         'tag_list' : [{ 'id' : x.id,
                                         'name' : x.name,
                                         'color': x.color,
                                        } for x in EventTag.objects.all()],
                         'event_list' : Event.objects.filter(timeslot__isnull=True).filter(conf_id=conf),
                         'time_list' : time_list,
                         'room_list' : room_list,
                         'user_list' : [{'name' : u.first_name + ' ' + u.last_name,
                                         'username' : u.username} for u in users],
                         'url_id' : url_id,
                     })

    @transaction.atomic
    @permission_required('confla.can_organize', raise_exception=True)
    def save_timetable(request, url_id):
        conf = get_conf_or_404(url_id)

        if(request.method == 'POST'):
            TimetableView.json_to_timeslots(request.POST['data'], url_id)
            return HttpResponseRedirect(reverse('confla:thanks'))

    @permission_required('confla.can_organize', raise_exception=True)
    def save_event(request, url_id):
        conf = get_conf_or_404(url_id)

        if request.method == 'POST':
            if request.POST['event_id'] == "0":
                # New event
                form = EventCreateForm(request.POST)
                if form.is_valid():
                    new_event = form.save(commit=False)
                    new_event.conf_id = conf
                    new_event.e_type_id = EventType.objects.all()[0]
                    new_event.lang = "cz"
                    if "tags" in request.POST:
                        new_event.prim_tag = EventTag(id=request.POST.getlist('tags')[0])
                    new_event.save()
                    form.save_m2m()
                    return HttpResponse(new_event.id)
                else:
                    return HttpResponseBadRequest(form.errors.as_ul())
            else:
                # Existing event
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
                    return HttpResponseRedirect(reverse('confla:thanks'))
                else:
                    return HttpResponseBadRequest(form.errors.as_ul())

    def json_to_timeslots(json_string, url_id):
        # JSON format: '[{"Room" : {"start" : "HH:MM", "end" : "HH:MM"}}]'
        conf = get_conf_or_404(url_id)

        json_obj = json.loads(json_string)
        # Delete all existing timeslots
        Timeslot.objects.filter(conf_id=conf).delete()
        # Create new timeslots from JSON
        for row in json_obj:
            # row: one row in the timeslot table
            # key: room shortname, also dictionary key for timeslots
            for key in row:
                newslot = Timeslot()
                newslot.event_id = Event.objects.get(id=row[key]['event'])
                newslot.room_id = Room.objects.get(shortname=key)
                newslot.conf_id = conf
                # Has to be like this or else django complains!
                start = datetime.strptime(row[key]['start'], "%H:%M")
                end = datetime.strptime(row[key]['end'], "%H:%M")
                date = datetime.strptime(row[key]['day'], "%A, %d.%m.")
                date = date.replace(year=conf.start_date.year)
                newslot.start_time = timezone.get_default_timezone().localize(datetime.combine(date, start.time()))
                newslot.end_time = timezone.get_default_timezone().localize(datetime.combine(date, end.time()))
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


class ImportView(generic.TemplateView):
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

    @permission_required('confla.can_organize', raise_exception=True)
    def import_view(request, url_id=None):
        template_name = 'confla/admin/import.html'
        if url_id:
            conf = get_conf_or_404(url_id)

        form = ImportFileForm()
        return render(request, template_name,
                        {   'url_id' : url_id,
                            'form'   : form,
                            })

    @permission_required('confla.can_organize', raise_exception=True)
    def oa_upload(request):
        if request.method == 'POST':
            form = ImportFileForm(request.POST, request.FILES)
            if form.is_valid():
                alerts = ImportView.oa2015(request.FILES['file'], overwrite=form.cleaned_data['overwrite'])
                return HttpResponse(alerts)
            else:
                # TODO: error checking
                return HttpResponseRedirect(reverse('confla:thanks'))

    @transaction.atomic
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
            start = datetime.strptime(slot['start_t'], "%H:%M")
            end = datetime.strptime(slot['end_t'], "%H:%M")
            newslot.start_time = timezone.get_default_timezone().localize(start)
            newslot.end_time = timezone.get_default_timezone().localize(end)
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
    @transaction.atomic
    def dv(json_string):
        # delete everyone excluding admin
        json_obj = json.loads(json_string)
        #room_list = ['D0206', 'D0207', 'A113', 'E105', 'D105', 'A112', 'E104', 'E112']
        # Setup a Conference if there is none
        try:
            conf = Conference.objects.get(url_id='Placeholder')
        except ObjectDoesNotExist:
            newconf = Conference()
            newconf.url_id = 'Placeholder'
            newconf.active = True
            newconf.name = "Placeholder"
            newconf.start_time = time(9, 0, 0)
            newconf.end_time = time(17, 30, 0)
            newconf.save()
            conf = newconf
        # Generate sessions
        for event in json_obj['sessions']:
            try:
                newevent = Event.objects.get(conf_id=conf, topic=event['topic'])
            except ObjectDoesNotExist:
                newevent = Event()
                newevent.conf_id = conf
                newevent.e_type_id, created = EventType.objects.get_or_create(name=event['type'])
                newevent.topic = event['topic']
                newevent.description = event['description']
                newevent.lang = event['lang']

                newevent.full_clean()
                newevent.save()

            # Create rooms
            room, created = Room.objects.get_or_create(shortname=event['room_short'])
            created, hr = HasRoom.objects.get_or_create(room=room, conference=conf, slot_length=3)

            try:
                newevent.timeslot
            except ObjectDoesNotExist:
                # Create timeslot for the event
                newslot = Timeslot()
                newslot.conf_id = conf
                newslot.room_id = Room.objects.get(shortname=event['room_short'])
                start = datetime.fromtimestamp(int(event['event_start']))
                end = datetime.fromtimestamp(int(event['event_end']))
                newslot.start_time = timezone.get_default_timezone().localize(start)
                newslot.end_time = timezone.get_default_timezone().localize(end)
                newslot.event_id = newevent
                newslot.full_clean()
                newslot.save()

            # Create speakers
            for speaker in event['speakers']:
                username = speaker.replace(" ", "")[:30]
                username = re.sub('[\W_]+', '', username)
                newuser, created = ConflaUser.objects.get_or_create(username=username)
                if created:
                    newuser.password = "blank"
                    newuser.first_name = speaker
                    newuser.full_clean()
                    newuser.save()
                newevent.speaker.add(newuser)

            if event['tags']:
                tags = event['tags'][0].split(",")
            else:
                tags = ['notag']

            # Create tags
            for tag in tags:
                tag = tag.strip()
                newtag, created = EventTag.objects.get_or_create(name=tag)
                if created:
                    newtag.color = "#%06x" % random.randint(0,0xFFFFFF)
                    newtag.full_clean()
                    newtag.save()
                newevent.tags.add(newtag)

            newevent.prim_tag = EventTag.objects.get(name=tags[0])
            newevent.save()   

        # Generate users
        users_list = json_obj['users']
        for user in users_list:
            username = user['name'].replace(" ", "")[:30]
            username = re.sub('[\W_]+', '', username)
            newuser, created = ConflaUser.objects.get_or_create(username=username)
            if created:
                newuser.password = "blank"
                newuser.first_name = user['name'][:30]
            newuser.company = user['company']
            newuser.position = user['position']
            newuser.picture = user['avatar']
            newuser.full_clean()
            newuser.save()

        # Setup proper start and end times of the conference
        first_slot = Timeslot.objects.filter(conf_id=conf).order_by("start_time")[0]
        last_slot = Timeslot.objects.filter(conf_id=conf).order_by("-end_time")[0]
        conf.start_date = first_slot.start_time.date()
        conf.end_date = last_slot.end_time.date()
        conf.save()

    @transaction.atomic
    def oa2015(csv_file, overwrite=False):
        # Setup a Conference if there is none
        try:
            conf = Conference.objects.get(url_id='oa2015')
        except ObjectDoesNotExist:
            newconf = Conference()
            newconf.start_date = date(2015, 11, 7)
            newconf.end_date = date(2015, 11, 8)
            newconf.start_time = time(8, 0, 0)
            newconf.end_time = time(20, 0, 0)
            newconf.url_id = 'oa2015'
            newconf.active = True
            newconf.name = "Openalt 2015"
            newconf.save()
            conf = newconf
            # Setup rooms
            room_list = ['D0206', 'D0207', 'A113', 'E105', 'D105', 'A112', 'E104', 'E112']
            for i in room_list:
                room, created = Room.objects.get_or_create(shortname=i)
                hr = HasRoom(room=room, conference=conf, slot_length=3)
                hr.save()

        events_created = 0
        events_modified = 0
        events_skipped = 0
        users_created = 0
        users_modified = 0
        users_skipped = 0

        f = io.TextIOWrapper(csv_file.file, encoding="utf-8")
        # Skip the headers
        next(f)
        next(f)
        next(f)
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            # Loop through each row of the csv file
            # Generate sessions

            # Create the speakers if not already in the db
            # First speaker
            username1 = row[9].replace(" ", "")[:30]
            username1 = re.sub('[\W_]+', '', username1)
            username2 = ''
            try:
                newuser = ConflaUser.objects.get(username=username1)
                if not overwrite:
                    users_skipped += 1
                    continue
            except ObjectDoesNotExist:
                newuser = ConflaUser()
                newuser.username = username1
                newuser.password = "blank"
                users_created += 1
            else:
                users_modified += 1

            newuser.first_name = row[9][:30]
            newuser.company = row[15]
            newuser.position = row[16]
            newuser.email = row[10]
            newuser.web = row[17].strip()
            if newuser.web and not newuser.web.startswith('http'):
                newuser.web = 'http://' + newuser.web
            newuser.facebook = row[18].strip()
            if newuser.facebook:
                if newuser.facebook.startswith('www.facebook'):
                    newuser.facebook = 'https://' + newuser.facebook
                elif not newuser.facebook.startswith('http'):
                    newuser.facebook = 'https://www.facebook.com/' + newuser.facebook
            newuser.twitter = row[19].strip()
            if newuser.twitter:
                if newuser.twitter.startswith('twitter'):
                    newuser.twitter = 'https://' + newuser.twitter
                elif not newuser.twitter.startswith('http'):
                    newuser.twitter = 'https://twitter.com/' + newuser.twitter
            newuser.linkedin= row[20].strip()
            if newuser.linkedin and not newuser.linkedin.startswith('http'):
                newuser.linkedin = 'https://' + newuser.linkedin
            newuser.google_plus= row[21].strip()
            if newuser.google_plus:
                if newuser.google_plus.startswith('plus.google'):
                    newuser.google_plus = 'https://' + newuser.google_plus
                elif not newuser.google_plus.startswith('http'):
                    newuser.google_plus = 'https://plus.google.com/' + newuser.google_plus
            if row[23]:
                # FIXME: Own avatar field
                newuser.github = row[23].strip()
            newuser.full_clean()
            newuser.save()
            # Second speaker
            if row[26]:
                username2 = row[26].replace(" ", "")[:30]
                username2 = re.sub('[\W_]+', '', username2)
                try:
                    newuser = ConflaUser.objects.get(username=username2)
                    if not overwrite:
                        users_skipped += 1
                        continue
                except ObjectDoesNotExist:
                    newuser = ConflaUser()
                    newuser.username = username2
                    newuser.password = "blank"
                    users_created += 1
                else:
                    users_modified += 1
                newuser.first_name = row[26][:30]
                newuser.company = row[31]
                newuser.position = row[32]
                newuser.email = row[27]
                newuser.web = row[33].strip()
                if row[33] and not newuser.web.startswith('http'):
                    newuser.web = 'http://' + newuser.web
                newuser.facebook = row[34].strip()
                if newuser.facebook:
                    if newuser.facebook.startswith('www.facebook'):
                        newuser.facebook = 'https://' + newuser.facebook
                    elif not newuser.facebook.startswith('http'):
                        newuser.facebook = 'https://www.facebook.com/' + newuser.facebook
                newuser.twitter = row[35].strip()
                if newuser.twitter:
                    if newuser.twitter.startswith('twitter'):
                        newuser.twitter = 'https://' + newuser.twitter
                    elif not newuser.twitter.startswith('http'):
                        newuser.twitter = 'https://twitter.com/' + newuser.twitter
                newuser.linkedin= row[36].strip()
                if newuser.linkedin and not newuser.linkedin.startswith('http'):
                    newuser.linkedin = 'https://' + newuser.linkedin
                newuser.google_plus= row[37].strip()
                if newuser.google_plus:
                    if newuser.google_plus.startswith('plus.google'):
                        newuser.google_plus = 'https://' + newuser.google_plus
                    elif not newuser.google_plus.startswith('http'):
                        newuser.google_plus = 'https://plus.google.com/' + newuser.google_plus
                if row[39]:
                    # FIXME: Own avatar field
                    newuser.github = row[39].strip()
                newuser.full_clean()
                newuser.save()

            # length of each event section
            event_len = 8
            # number of events
            event_num = 3
            # index of the first event
            sp = 42
            for i in range(0,event_len*event_num,event_len):
                # Loop through all events in the row
                if not row[sp+i+1]:
                    # There are no more events left
                    break;
                # If an event with the same topic already exists in the conference
                try:
                    newevent = Event.objects.get(topic=row[sp+2+i], conf_id=conf)
                    # and if overwrite argument is not set, skip event
                    if not overwrite:
                        events_skipped += 1
                        continue
                except ObjectDoesNotExist:
                    newevent = Event()
                    events_created += 1
                else:
                    events_modified += 1
                newevent.conf_id = conf
                etype, created = EventType.objects.get_or_create(name=row[sp+1+i])
                newevent.e_type_id = etype
                newevent.topic = row[sp+2+i]
                newevent.description = row[sp+3+i]
                newevent.lang = 'CZ'
                newevent.reqs = row[sp+6+i]
                notes = 'Delka prednasky: ' + row[sp+5+i] + '\n'
                # Get preferred day from both speakers if possible
                notes = notes + 'Preferovany den: ' + row[14]
                if row[32]:
                    notes = notes + '; ' + row[32]
                notes = notes + '\n'
                notes = notes + 'Poznamky: ' + row[sp+7+i] + '\n'
                newevent.notes = notes
                newevent.full_clean()
                newevent.save()

                # Add speakers
                newevent.speaker.add(ConflaUser.objects.get(username=username1))
                if username2:
                    newevent.speaker.add(ConflaUser.objects.get(username=username2))
                newevent.save()

                # Add tag
                if row[sp+i]:
                    etag, created = EventTag.objects.get_or_create(name=row[sp+i])
                    if created:
                        # Create a nice random colour
                        r = lambda: (random.randint(0,255)+255) // 2
                        etag.color = '#%02x%02x%02x' % (r(),r(),r())
                        etag.save()
                    # Remove any existing tags from the event
                    newevent.tags.clear()
                    newevent.tags.add(etag)
                    newevent.prim_tag = etag
                    newevent.save()

        check = '<i class="fa fa-check-circle fa-lg"></i>'
        warning = '<i class="fa fa-exclamation-triangle fa-lg"></i>'
        created = '<div class="alert alert-success">' + check + ' Events created: ' + str(events_created)
        created += ', Users created: ' + str(users_created) + '</div>'
        modified ='<div class="alert alert-success">' + check + ' Events modified: ' + str(events_modified)
        modified += ', Users modified: ' + str(users_modified) + '</div>'
        skipped = '<div class="alert alert-warning">' + warning + ' Events skipped: ' + str(events_skipped)
        skipped += ', Users skipped: ' + str(users_skipped) + '</div>'
        if overwrite:
            return '<div class="import-alerts">'+ created + modified + '</div>'
        else:
            return '<div class="import-alerts">'+ created + skipped + '</div>'

class ExportView(generic.TemplateView):
    @permission_required('confla.can_organize', raise_exception=True)
    def export_view(request, url_id):
        template_name = 'confla/admin/export.html'
        conf = get_conf_or_404(url_id)

        return render(request, template_name,{ 'url_id' : url_id })

    def m_app(request, url_id):
        conf = get_conf_or_404(url_id)

        result = {}
        tz = timezone.get_default_timezone()
        rfc_time_format = "%a, %d %b %Y %X %z"
        # Export events
        result['sessions'] = []
        slots = Timeslot.objects.filter(conf_id=conf)
        for slot in slots:
            if slot.room_id:
                event = slot.event_id
                session = {}
                session['session_id'] = event.pk
                session['lang'] = event.lang
                session['type'] = event.e_type_id.name
                # Primary tag color
                if event.prim_tag:
                    session['room_color'] = event.prim_tag.color 
                    session['track'] = event.prim_tag.name
                else:
                    session['room_color'] = '#787878'
                    session['track'] = ''
                session['room'] = slot.room_id.shortname
                session['room_short'] = slot.room_id.shortname
                session['speakers'] = [x.first_name for x in event.speaker.all()]
                session['description'] = event.description
                session['tags'] = [x.name for x in event.tags.all()]
                session['topic'] = event.topic
                start_time = slot.start_time.astimezone(tz)
                end_time = slot.end_time.astimezone(tz)
                session['event_start'] = int(start_time.timestamp())
                session['event_start_rfc'] = start_time.strftime(rfc_time_format)
                session['event_end'] = int(end_time.timestamp())
                session['event_end_rfc'] = end_time.strftime(rfc_time_format)
                session['reqs'] = event.reqs
                session['video'] = event.video
                session['slides'] = event.slides
                result['sessions'].append(session)

        # Export days
        result['days'] = [ int(datetime.combine(x, time()).timestamp())
                            for x in conf.get_datetime_date_list()]

        # Export users
        result ['users'] = []
        for usr in ConflaUser.objects.all().exclude(username="admin"):
            user = {}
            user['username'] = usr.username
            user['name'] = usr.first_name
            user['position'] = usr.position
            user['company'] = usr.company
            user['joined'] = usr.date_joined.astimezone(tz).isoformat()[:19].replace('T', ' ')
            if usr.last_login:
                user['lastactive'] = usr.last_login.astimezone(tz).isoformat()[:19].replace('T', ' ')
            else:
                user['lastactive'] = ''
            # FIXME: Own avatar field
            user['avatar'] = usr.github
            user['web'] = usr.web
            user['facebook'] = usr.facebook
            user['twitter'] = usr.twitter
            user['google_plus'] = usr.google_plus
            user['linkedin'] = usr.linkedin
            result['users'].append(user)

        # Export about
        # TODO: Proper about section once we have it
        result['about'] = [{ 'title' : conf.name,
                             'text'  : 'placeholder'
                           }]

        # RSS
        result['rss'] = []

        # Generate checksum
        result['checksum'] = hashlib.sha1(json.dumps(result).encode("utf-8")).hexdigest()

        return HttpResponse(json.dumps(result), content_type="application/json")

    def csv(request, url_id):
        conf = get_conf_or_404(url_id)

        iostr = io.StringIO()
        writer = csv.writer(iostr, quoting=csv.QUOTE_NONNUMERIC)
        slot_list = {}
        rooms = conf.rooms.all()
        header = []
        for room in rooms:
            slot_list[room.shortname] = Timeslot.objects.filter(conf_id=conf, room_id=room).order_by("start_time")
            header.append('time')
            header.append(room.shortname)
        writer.writerow(header)
        time_list = []
        start_list = conf.get_datetime_time_list()
        for date in conf.get_datetime_date_list():
            time_dict = {}
            time_dict["day"] = date.strftime("%A, %d.%m.")
            time_dict["list"] = []
            for start_time in start_list:
                time = {}
                time['full'] = datetime.combine(date, start_time).strftime("%x %H:%M")
                time['slots'] = []
                for room in rooms:
                    for slot in slot_list[room.shortname]:
                        if slot.get_start_datetime == time['full']:
                            end_time = slot.get_end_time
                            time['slots'].append(start_time.strftime("%H:%M") + ' - ' + end_time)
                            time['slots'].append(slot.event_id.topic)
                            break
                    else:
                        time['slots'].append('')
                        time['slots'].append('')
                for slot in time['slots']:
                    if slot:
                        time_dict['list'].append(time)
                        writer.writerow(time['slots'])
                        break;

            time_list.append(time_dict)
        return HttpResponse(iostr.getvalue(), content_type="text/csv")
