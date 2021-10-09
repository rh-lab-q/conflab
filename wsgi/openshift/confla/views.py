import json
import random
import re
import hashlib
import csv
import io
import urllib
import http.client
import pprint

from datetime import datetime, date, time

from django.db.models import Count
from django.template.loader import render_to_string
from django.template.defaultfilters import date as _date
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.urls import reverse
from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.db import transaction
from unidecode import unidecode


from confla.forms import *
from confla.models import *
from confla.view_utils import get_conf_or_404

class AdminView(generic.TemplateView):

    @permission_required('confla.can_organize', raise_exception=True)
    def dashboard(request, url_id=None):
        conf = None
        events = None
        if url_id:
            conf = get_conf_or_404(url_id)
            speakers = conf.get_speakers
#            tags = EventTag.objects.filter(events__conf_id=conf, events__timeslot__isnull=False).distinct()
            tags = EventTag.objects.filter(event__conf_id=conf).values('name', 'color').annotate(count=Count('pk')).order_by('-count')
        else:
            events = Event.objects.all()
            speakers = ConflaUser.objects.all()
            tags = EventTag.objects.all()

        return render(request, "confla/admin/dashboard.html",
                        {   'url_id' : url_id,
                            'conf' : conf,
                            'events' : events,
                            'speakers' : speakers,
                            'tags': tags,
                            'conf_list' : Conference.objects.all().order_by('start_date'),
                        })

    @permission_required('confla.can_organize', raise_exception=True)
    def users(request, url_id=None):
        if url_id:
            conf = get_conf_or_404(url_id)
            users = ConflaUser.objects.filter(events__conf_id=conf).distinct().order_by('username')

        else:
            conf = None
            users = ConflaUser.objects.distinct().order_by('username')
        return render(request, "confla/admin/users.html",
                    {    'url_id' : url_id,
                         'conf': conf,
                         'users': users,
                         'conf_list' : Conference.objects.all().order_by('start_date'),
                    })

    @permission_required('confla.can_organize', raise_exception=True)
    def conf_list(request):
        return render(request, "confla/admin/conf_list.html",
                    {
                         'conf_list' : Conference.objects.all().order_by('-start_date'),
                    })
    def default_tags(request):
        tag, created_id = EventTag.objects.get_or_create(name='Otevřený a svobodný software', color ='#10753f')
        tag, created_id = EventTag.objects.get_or_create(name='IoT a Hnutí tvůrců', color = '#2f62ae')
        tag, created_id = EventTag.objects.get_or_create(name='Vzdělávání', color = '#be1e2d')
        tag, created_id = EventTag.objects.get_or_create(name='Bezpečnost a soukromí', color = '#57585a')
        tag, created_id = EventTag.objects.get_or_create(name='Otevřená společnost, komunity a data', color = '#d37a6a')
        tag, created_id = EventTag.objects.get_or_create(name='OpenMobility', color = '#92378b')
        tag, created_id = EventTag.objects.get_or_create(name='Open Science', color = '#f57900')
        tag, created_id = EventTag.objects.get_or_create(name='Otevřené mapy', color = '#000000')
        tag, created_id = EventTag.objects.get_or_create(name='Otevřené umění a tvorba', color = '#edd400')

        return render(request, "confla/admin/import_response.html",
                    {
                        'message': 'default tags was created'
                    })

class ConferenceView(generic.TemplateView):
    @permission_required('confla.can_organize', raise_exception=True)
    def create_conf(request):
        template_name = 'confla/admin/create_conf.html'
        return render(request, template_name,
                     {
                        'form' : ConfCreateForm(),
                        'conf_list' : Conference.objects.all().order_by('start_date'),
                        'rooms' : [{'id' : r.id,
                                    'name' : r.shortname} for r in Room.objects.all()],
                        })

    def edit_conf(request, url_id):
        template_name = 'confla/admin/create_conf.html'
        conf = get_conf_or_404(url_id)
        # Rooms used by the conference
        rooms_exis = conf.rooms.all().order_by('hasroom__order') 
        rooms_ids = conf.rooms.all().values('id')
        # Rooms possible to be added to the conference
        rooms_adds = Room.objects.exclude(id__in=rooms_ids)
        form = ConfCreateForm(instance=conf)
        # Uses | to join the two querysets
        form.base_fields['rooms'].queryset = rooms_exis | rooms_adds
        rooms = Room.objects.all()
        return render(request, template_name,
                     {
                        'form' : form,
                        'conf_list' : Conference.objects.all().order_by('start_date'),
                        'url_id' : url_id,
                        'conf' : conf,
                        'rooms' : [{'id' : r.id,
                                    'name' : r.shortname} for r in rooms],

                     })

    @transaction.atomic
    @permission_required('confla.can_organize', raise_exception=True)
    def save_conf(request, url_id=None):
        try:
            conf = Conference.objects.get(url_id=url_id)
        except ObjectDoesNotExist:
            conf = None
        form = ConfCreateForm(request.POST, request.FILES, instance=conf)
        if form.is_valid():
            conf = form.save(commit=False)
            conf.save()
            # Delete existing HasRoom relations
            HasRoom.objects.filter(conference=conf).delete()
            rooms = []
            for room in request.POST.getlist('rooms'):
                rooms.append(Room.objects.get(id=room))
            for i, room in enumerate(rooms):
                hr, created = HasRoom.objects.get_or_create(room=room, conference=conf, slot_length=3)
                hr.order = i;
                hr.save()
        else:
            template_name = 'confla/admin/create_conf.html'
            return render(request, template_name,
                 {
                    'form' : form,
                    'conf_list' : Conference.objects.all().order_by('start_date'),
                 })
        url_id = request.POST['url_id'] 
        return HttpResponseRedirect(reverse('confla:dashboard',kwargs={'url_id' : url_id}))

    @permission_required('confla.can_organize', raise_exception=True)
    def create_room(request):
        room, created = Room.objects.get_or_create(shortname=request.POST['data'])
        return HttpResponse(room.id)

class EventEditView(generic.TemplateView):
    template_name = 'confla/event_edit.html'

    @permission_required('confla.can_organize', raise_exception=True)
    def create_event_tag(request):
        r = lambda: (random.randint(0,255)+255) // 2
        c = '#%02x%02x%02x' % (r(),r(),r())
        tag, created_id = EventTag.objects.get_or_create(name=request.POST['data'], color = c )
        return HttpResponse(json.dumps({'name' : tag.name, 'color': tag.color, 'id': tag.id}), content_type="application/json")

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
    def splash_view(request, url_id):
        conf = get_conf_or_404(url_id)

        events = len(Timeslot.objects.filter(event_id__conf_id=conf))
        speakers = len(ConflaUser.objects.filter(events__conf_id=conf,
                                                 events__timeslot__isnull=False).distinct())
        topics = len(EventTag.objects.filter(events__conf_id=conf,
                            events__timeslot__isnull=False).distinct())
        return render(request, AboutView.template_name,
                        {'url_id' : url_id,
                         'conf' : conf,
                         'events' : events,
                         'speakers' : speakers,
                         'topics' : topics,
                            })

class IndexView(generic.TemplateView):
    template_name = 'confla/index.html'
    def my_view(request):
        conf_list = Conference.objects.filter(active=True).order_by("-start_date")
        if len(conf_list) == 1:
            return HttpResponseRedirect(reverse('confla:splash',kwargs={'url_id' : conf_list[0].url_id}))
        else:
            return render(request, IndexView.template_name, {'conf_list' : conf_list})

class CfpView(generic.TemplateView):
    # TODO: Combine these two methods
    @login_required
    def save_form_and_register(request, url_id):
        conf = get_conf_or_404(url_id)

        if request.method == 'POST':
            event_form = EventFullEditForm(data=request.POST, instance=conf)
#            user_form = RegisterForm(request.POST)
#            paper_form = PaperForm(request.POST)
            if event_form.is_valid():
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(event_form);
                e = event_form.save();
                pp.pprint(e)
#            if user_form.is_valid() and paper_form.is_valid():
#                user = user_form.save()
#                paper = paper_form.save(commit=False)
#                paper.user_id = user.id;
#                paper.save()
                return HttpResponseRedirect(reverse('confla:index'))
        else:
            event_form = EventFullEditForm(data=request.POST, instance=conf)
#            user_form = RegisterForm()
#            paper_form = PaperForm()

        return render(request, 'confla/reg_talk.html', {
#            'user_form': user_form,
#            'paper_form': paper_form,
            'event_form': event_form,
            'url_id' : url_id,
            'conf' : conf,
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
                return HttpResponseRedirect(reverse('confla:splash', kwargs={'url_id': url_id}))
        else:
            paper_form = PaperForm()

        return render(request, 'confla/reg_talk.html', {
            'paper_form': paper_form,
            'url_id' : url_id,
            'conf' : conf,
        })

class VolunteerView(generic.TemplateView):
    template_name = 'confla/volunteer.html'

    @permission_required('confla.can_volunteer', raise_exception=True)
    def my_view(request):
        return render(request, VolunteerView.template_name)

class PlacesView(generic.TemplateView):
    def osm(request, url_id):
        conf = get_conf_or_404(url_id)
        return render(request, 'confla/map.html', {
            'url_id' : url_id,
            'conf' : conf,
        })
    def table(request):
        return render(request, 'confla/admin/places.html', {
            'places' : GeoPoint.objects.all()
        })

class IconsView(generic.TemplateView):
    def table(request):
        return render(request, 'confla/admin/geo_icons.html', {
            'icons' : GeoIcon.objects.all()
        })

class PagesView(generic.TemplateView):

    def content(request, url_id, page):
        conf = get_conf_or_404(url_id)
        pageObject = Page.objects.get(id=page);

        return render(request, 'confla/page.html', {
            'url_id' : url_id,
            'conf' : conf,
            'page' : pageObject,
        })

    def pages_list(request, url_id):
        conf = get_conf_or_404(url_id)
#        pageObject = Page.objects.get(id=page);


        return render(request, 'confla/admin/pages.html', {
            'url_id' : url_id,
            'conf' : conf,
            'pages' : Page.objects.filter(conf_id=conf),
        })

    def edit_page(request, url_id, page):
        conf = get_conf_or_404(url_id)
        pageObject = Page.objects.get(id=page);

        return render(request, 'confla/admin/page.html', {
            'url_id' : url_id,
            'conf' : conf,
            'page' : pageObject,
            'form': PageForm(instance=pageObject),
        })

    def save_page(request, url_id, page):
        print(request);
        pageObject = Page.objects.get(id=page);
        form = PageForm(request.POST, request.FILES, instance=pageObject)
        if form.is_valid():
            page = form.save(commit=False)
            page.save()

        return HttpResponseRedirect(reverse('confla:admin_pages',kwargs={'url_id' : url_id}))


class EventView(generic.TemplateView):

    def event_list(request, url_id):
        template_name = 'confla/event_list.html'
        conf = get_conf_or_404(url_id)
        days = []
        events = Event.objects.filter(conf_id=conf, timeslot__isnull=False).order_by('timeslot__start_time')
        if events:
            current_date = events[0].timeslot.start_time.date()
            current_date_output = current_date.strftime("%A, %d.%m.")
            day = { 'date' : current_date_output,
                    'events' : [], }
            for event in events:
                if event.timeslot.start_time.date() > current_date:
                    # New day
                    current_date = event.timeslot.start_time.date()
                    current_date_output = current_date.strftime("%A, %d.%m.")
                    days.append(day)
                    day = { 'date' : current_date_output,
                            'events' : [], }
                day['events'].append(event)

        # Append last day
        days.append(day)
        return render(request, template_name, {
                    'days': days,
                    'tag_list' : EventTag.objects.filter(event__conf_id=conf).distinct(),
                    'url_id' : url_id,
                    'conf' : conf,
                    })

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
        if event_id > 0:
            event = Event.objects.get(id=int(request.POST['data']))
            form = EventCreateForm(instance=event)
        else:
            event = None
            form = EventCreateForm()

        return render(request, template_name,
                        {'event' : event,
                         'event_id': event_id,
                         'form'  : form,
                         'url_id' : url_id,
                        })

class ScheduleView(generic.TemplateView):
    template_name = 'confla/user_sched.html'

    def my_view(request, url_id):
        conf = get_conf_or_404(url_id)
        if (not conf.has_datetimes()):
            raise Http404

        delta = timedelta(minutes=conf.timedelta)
        slot_list = {}
        rooms = conf.rooms.all().order_by('hasroom__order')
        for room in rooms:
            slot_list[room.shortname] = Timeslot.objects.filter(conf_id=conf, room_id=room).order_by("start_time")
        time_list = []
        start_list = conf.get_datetime_time_list()
        for date in conf.get_datetime_date_list():
            last_end = None
            time_dict = {}
            time_dict["day"] = date.strftime("%A, %d.%m.")
            time_dict["list"] = []
            for start_time in start_list:
                time = {}
                tz = timezone.get_default_timezone()
                slot_dt = tz.localize(datetime.combine(date, start_time))
                time['short'] = start_time.strftime("%H:%M") 
                time['full'] = slot_dt.strftime("%x %H:%M")
                time['dt'] = slot_dt
                time['empty'] = True
                time['slots'] = []
                for i, room in enumerate(rooms):
                    time['slots'].append([])
                    for slot in slot_list[room.shortname]:
                        if slot_dt <= slot.get_start_datetime < slot_dt+delta:
                            time['slots'][i].append(slot)
                            time['empty'] = False
                            if not last_end or last_end < slot.end_time:
                                last_end = slot.end_time
                time_dict["list"].append(time)

            # Edit starting slots only when there are events scheduled
            if last_end:
                # Remove empty slots from the start
                for i, time in enumerate(time_dict['list']):
                    if not time['empty']:
                        # Slice the list
                        time_dict['list'] = time_dict['list'][i:]
                        break

                # Remove empty slots from the end
                for i, time in enumerate(time_dict['list'][::-1]):
                    if not (time['empty'] and last_end < time['dt']+delta):
                        if i is not 0:
                            # Slice only when there is something to slice
                            time_dict['list'] = time_dict['list'][:-i]
                        break

                # Show day only when there are events scheduled
                time_list.append(time_dict)

        return render(request, ScheduleView.template_name,
                    {    'time_list' : time_list,
                         'legend_list' : EventTag.objects.filter(event__conf_id=conf).distinct(),
                         'room_list' : [{'conf' : conf,
                                         'room' : x} for x in rooms],
                         'url_id' : url_id,
                         'conf' : conf,
                         })

    def list_view(request, url_id, id=None):
        conf = get_conf_or_404(url_id)
        if (not conf.has_datetimes()):
            raise Http404

        time_list = []
        # Distinct ordered datetime list for the current conference
        if id:
            slot_list = Timeslot.objects.filter(conf_id=conf, event_id__tags__id=id)
        else:
            slot_list = Timeslot.objects.filter(conf_id=conf)
        start_list = slot_list.order_by('start_time').values_list('start_time', flat=True).distinct()
        for date in conf.get_date_list():
            time_dict = {}
            time_dict['day'] = date
            time_dict['list'] = []
            for start_time in start_list:
                start_time = start_time.astimezone(timezone.get_default_timezone())
                if start_time.strftime('%A, %d.%m.') == date:
                    time = {}
                    time['short'] = start_time.strftime('%H:%M') 
                    time['full'] = start_time.strftime('%x %H:%M') 
                    time['slots'] = []
                    for slot in slot_list:
                        if slot.get_start_datetime.strftime('%x %H:%M') == time['full']:
                            time['slots'].append(slot)
                    time_dict['list'].append(time)
            if time_dict['list']:
                time_list.append(time_dict)

        return render(request, 'confla/schedlist.html',
                      {  'time_list' : time_list, 
                         'tag_list' : EventTag.objects.all(),
                         'legend_list' : EventTag.objects.filter(event__conf_id=conf).distinct(),
                         'room_list' : [{'conf' : conf,
                                         'room' : x} for x in conf.rooms.all()],
                         'url_id' : url_id,
                         'conf' : conf,
                         'tag_id' : id,
                         })

class LoginView(generic.TemplateView):
    template_name = 'confla/login.html'

    def my_view(request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('confla:users'))
        else:
            return render(request, 'confla/login.html', {
            'form' : AuthForm(),
        })

    #TODO: OpenSSL,  or some other crypto for POST
    def auth_and_login(request):
        if not(request.method == "POST"):
            return HttpResponseRedirect(reverse('confla:login'))

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
            if request.POST['next'] is not "":
                redirect = request.POST['next']
            else:
                if user.has_perm('confla.can_organize'):
                    redirect = reverse('confla:org_conf_list')
                else:
                    redirect = reverse('confla:users')

            # all is OK, redirect the logged in user to the user site
            return HttpResponseRedirect(redirect)

    def logout(request):
        logout(request)
        return HttpResponseRedirect(reverse('confla:login'))

class UserView(generic.TemplateView):
    template_name = 'confla/base.html'

    @login_required
    def my_view(request):
        user = request.user
        return render(request, 'confla/user_dashboard.html', 
            {
                'conf_list' : Conference.objects.filter(event__speaker=user).order_by('start_date').distinct(),
                'confs' : Conference.objects.all(),
                'favorites' : Favorite.objects.filter(user=user),
                'speaker_events' : Event.objects.filter(speaker=user),
#                'events' : Timeslot.objects.filter(event_id__speaker=user)
                'user' : ConflaUser.objects.get(username=user),
            })

    @transaction.atomic
    def add_email(request, user, address):
        email = EmailAdress()
        email.user = user
        email.address = address
        email.is_active = False
        email.full_clean()
        email.activation_token = default_token_generator.make_token(user)
        email.save()
        url = request.build_absolute_uri(reverse('confla:activate_email',
                                         kwargs={'token' : email.activation_token}))
        # Try sending activation token
        try:
            # TODO: Proper email body
            send_mail('Confla: Activation Email',
                      url,
                      'cmconflab@gmail.com',
                      [email.address])
        except ConnectionRefusedError:
            # Email not set up properly in settings.py
            # FIXME: Dont activate email when live
            email.is_active = True
            email.save()
            # Debugging output
            print(email.activation_token)

        return email

    @transaction.atomic
    @login_required
    def delete_email(request, url_username, id):
        user = ConflaUser.objects.get(username=url_username)
        email = user.emailadress_set.filter(id=id)
        # Don't allow to edit other persons' information without permission
        if user != request.user and not request.user.has_perm('confla.can_organize'):
            raise PermissionDenied

        # Check if the address actually belongs to the user
        if not email:
            raise PermissionDenied

        email.delete()
        return HttpResponseRedirect(reverse('confla:profile', kwargs={'url_username' : url_username}))


    def set_email_primary(request, url_username, id):
        user = ConflaUser.objects.get(username=url_username)
        email = user.emailadress_set.filter(id=id)
        # Don't allow to edit other persons' information without permission
        if user != request.user and not request.user.has_perm('confla.can_organize'):
            raise PermissionDenied

        # Check if the address actually belongs to the user
        if not email:
            raise PermissionDenied

        # If the email is inactive, don't make it primary
        if email.first().is_active:
            user.email = email.first().address
            user.save()
        return HttpResponseRedirect(reverse('confla:profile', kwargs={'url_username' : url_username}))

    @login_required
    def view_profile(request, url_username):
        user = ConflaUser.objects.get(username=url_username)
        # Don't allow to view/edit other persons' information without permission
        if user != request.user and not request.user.has_perm('confla.can_organize'):
            raise PermissionDenied
        if request.method == 'POST':
            if 'submit-email' in request.POST:
                UserView.add_email(request, user, request.POST['new_email'])
            else:
                form = ProfileForm(request.POST, request.FILES, instance=user)
                if form.is_valid():
                    user = form.save(commit=False)
                    user.save()
            # TODO: make own "Your changes have been saved." page
            return HttpResponseRedirect(reverse('confla:profile', kwargs={'url_username': url_username}))
        else:
                form = ProfileForm(instance=user)
                email_form = EmailForm()

        return render(request, 'confla/profile.html',{
            'form' : form,
            'url_user' : user,
            'email_list' : EmailAdress.objects.filter(user=request.user),
            'email_form' : email_form,
            })

    def speaker_grid(request, url_id):
        template_name = 'confla/speaker_grid.html'

        conf = get_conf_or_404(url_id)

        speakers = ConflaUser.objects.filter(events__conf_id=conf, events__timeslot__isnull=False).distinct().order_by('username')
        return render(request, template_name, {
                        'speakers' : speakers,
                        'url_id' : url_id,
                        'conf' : conf,
                        })

    def speaker_list(request, url_id):
        template_name = 'confla/speaker_list.html'

        conf = get_conf_or_404(url_id)

        speakers = ConflaUser.objects.filter(events__conf_id=conf, events__timeslot__isnull=False).distinct().order_by('username')
        return render(request, template_name, {
                        'speakers' : speakers,
                        'url_id' : url_id,
                        'conf' : conf,
                        })

class RegisterView(generic.TemplateView):

    @transaction.atomic

    def reset_password2(request, email_address, token):
        email = get_object_or_404(EmailAdress, address=email_address, activation_token=token)
        if default_token_generator.check_token(email.user, token):
            password = ConflaUser.objects.make_random_password()
            email.user.is_active = True
            email.user.last_login = datetime.now()
            email.user.set_password(password)
            email.user.save();
            email.is_active = True
            email.save()
            user = authenticate(username=email.user,password=password)
            login(request, user)
            return render(request, 'confla/message.html', {
                'message': _('Your new password is ') + password,
            })
        else:
            return render(request, 'confla/message.html', {
                'type': 'error',
                'message': _('Invalid token'),
            })

    def reset_password(request):
        if request.method == 'POST': # the form was submitted
            emails = EmailAdress.objects.filter(address=request.POST['email'])
            if (len(emails) == 1):
                emails[0].is_active = False
                emails[0].activation_token = default_token_generator.make_token(emails[0].user)
                emails[0].save()
                url = request.build_absolute_uri(reverse('confla:reset_password2', kwargs={'email_address': emails[0].address, 'token': emails[0].activation_token}))
                html_message = 'Someone requested reset of your password. Here is a link to <a href="%s">password reset</a>' % url
                message = 'Someone requested reset of your password. Here is a link to password reset: %s' % url
                try:
                    send_mail(
                        subject='Conflab reset of password',
                        message=message,
                        html_message=html_message,
                        from_email=settings.EMAIL_HOST_EMAIL,
                        recipient_list=[emails[0].address],
                        fail_silently=False,
                    )
                    return render(request, 'confla/message.html', {
                        'message': _('Reset email was sent')
                    })
                except ConnectionRefusedError:
                    print(url)
                    return render(request, 'confla/message.html', {
                        'type': 'error',
                        'message': _('Connection refused')
                    })

        return render(request, 'confla/reset_password.html', {
            'form' : ResetPasswordForm(request.POST),
        })

    @transaction.atomic
    def user_register(request):
        if request.method == 'POST': # the form was submitted
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.is_active = True
                user.save()
                try:
                    UserView.add_email(request, user, user.email)
                except ValidationError as e:
                    user.delete()
                    errors = []
                    for key in e.args[0]:
                        errors += e.args[0][key]
                    form.errors['__all__'] = form.error_class(errors)
                    return render(request, 'confla/register.html', {
                         'form' : form})

                user = authenticate(username=request.POST['username'],
                    password=request.POST['password'])
                login(request, user)

                return HttpResponseRedirect(reverse('confla:index'))
        else:
            form = RegisterForm()

        return render(request, 'confla/register.html', {
            'form' : form,
        })

    @transaction.atomic
    def activate_email(request, token):
        # Get an email address object from the token
        email = get_object_or_404(EmailAdress, activation_token=token)
        if default_token_generator.check_token(email.user, token):
            email.user.is_active = True
            # Make sure the code can't be used again
            email.user.last_login = datetime.now()
            email.user.save()
            email.is_active = True
            email.save()
        else:
            raise Http404

        return HttpResponseRedirect(reverse('confla:users'))

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
        if (not conf.has_datetimes()):
            return render(request, TimetableView.template_name,
                     { 'conf'      : conf,
                       'url_id' : url_id,
                     })

        delta = timedelta(minutes=conf.timedelta)
        users = ConflaUser.objects.all()
        tags = EventTag.objects.all()
        rooms = conf.rooms.all().order_by('hasroom__order')
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
                tz = timezone.get_default_timezone()
                slot_dt = tz.localize(datetime.combine(date, start_time))
                time['short'] = start_time.strftime("%H:%M") 
                time['full'] = slot_dt.strftime("%x %H:%M")
                time['dt'] = slot_dt
                time['slots'] = []
                for i, room in enumerate(rooms):
                    time['slots'].append([])
                    for slot in slot_list[room.shortname]:
                        if slot_dt <= slot.get_start_datetime < slot_dt+delta:
                            time['slots'][i].append(slot)
                time_dict["list"].append(time)
            time_list.append(time_dict)
        room_list = [{'slot_len' : x.hasroom_set.get(conference=conf).slot_length,
                      'room' : x} for x in rooms]
        return render(request, TimetableView.template_name,
                      {  'conf'      : conf,
                         'event_create' : EventCreateForm(),
                         'tag_list' : [{ 'id' : x.id,
                                         'name' : x.name,
                                         'color': x.color,
                                         'fg_color': x.fg_color(),
                                        } for x in EventTag.objects.all()],
                         'legend_list' : EventTag.objects.filter(event__conf_id=conf).distinct(),
                         'event_list' : Event.objects.filter(timeslot__isnull=True).filter(conf_id=conf),
                         'time_list' : time_list,
                         'room_list' : room_list,
                         'user_list' : [{'name' : (u.first_name + ' ' + u.last_name).strip(),
                                         'username' : u.username} for u in users],
                         'url_id' : url_id,
                         'conf_list' : Conference.objects.all().order_by('start_date'),
                     })

    @transaction.atomic
    @permission_required('confla.can_organize', raise_exception=True)
    def save_timetable(request, url_id):
        conf = get_conf_or_404(url_id)

        if(request.method == 'POST'):
            TimetableView.json_to_timeslots(request.POST['data'], url_id)
            # Update JSON export
            ExportView.generate_json(request, url_id)
            return HttpResponseRedirect(reverse('confla:splash', kwargs={'url_id': url_id}))

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
                    result = {  'start_pos' : '',
                                'start_time' : '',
                                'end_time' : '',
                                'error' : '',
                                'style' : '',
                                }
                    event = form.save(commit=False)
                    if 'tags' in request.POST:
                        event.prim_tag = EventTag(id=request.POST.getlist('tags')[0])
                    else:
                        event.prim_tag = None
                    event.save()
                    form.save_m2m()
                    # Setup data needed to move the event to a slot
                    start = event.timeslot.get_start_datetime.time()
                    end = event.timeslot.get_end_datetime.time()
                    new_start = datetime.strptime(request.POST['start_time'], '%H:%M').time()
                    new_end = datetime.strptime(request.POST['end_time'], '%H:%M').time()
                    delta = timedelta(minutes=conf.timedelta)
                    dt = datetime.now()
                    start_list = conf.get_datetime_time_list()
                    for i, start_time in enumerate(start_list):
                        start_time_dt = (datetime.combine(dt, start_time) + delta).time()
                        if start_time <= new_start < start_time_dt:
                            result['start_pos'] = i+1
                            result['start_time'] = request.POST['start_time']
                            result['end_time'] = request.POST['end_time']
                            # Get grid offset for the event
                            time_offset = (datetime.combine(dt, new_start) - datetime.combine(dt, start_time)).seconds/60
                            offset = (time_offset * 31)/conf.timedelta
                            if offset == 1:
                                offset = 0
                            # CSS styles
                            height = str(31*event.timeslot.length-1) + 'px;'
                            result['style'] = 'top : ' + str(offset) + 'px;' + 'height : ' + height
                            break;
                    else:
                        # FIXME: Better error message
                        result['error'] = 'Wrong start time'

                    return HttpResponse(json.dumps(result), content_type="application/json")
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
                        "diaspora" : "",
                        "facebook" : "",
                        "twitter" : "",
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
        conf = get_conf_or_404(url_id)

        form = ImportFileForm()
        return render(request, template_name,
                        {   'url_id' : url_id,
                            'form'   : form,
                            'conf' : conf,
                            'conf_list' : Conference.objects.all().order_by('start_date'),
                            'tag_count': len(EventTag.objects.all())
                            })

    @permission_required('confla.can_organize', raise_exception=True)
    def json_upload(request, url_id=None):
        if request.method == 'POST':
            form = ImportFileForm(request.POST, request.FILES)
            if form.is_valid():
                alerts = ImportView.json(request,
                                         request.FILES['file'],
                                         overwrite=form.cleaned_data['overwrite'],
                                         url_id=url_id)
                return HttpResponse(alerts)
            else:
                # TODO: error checking
                return HttpResponseRedirect(reverse('confla:index'))

    @transaction.atomic
    def json(request, json_file, overwrite, url_id):
        f = io.TextIOWrapper(json_file.file, encoding="utf-8")
        json_string = f.read()
        json_obj = json.loads(json_string)

        events_created = 0
        events_modified = 0
        events_skipped = 0
        events_collisions = 0
        users_created = 0
        users_modified = 0
        users_skipped = 0
        users_collisions = 0

        conf = Conference.objects.get(url_id=url_id)



        # Generate users
        user_list = []
        users_list = json_obj['users']
        for user in users_list:
            username = user['name'].replace(" ", "")[:30]
            if not username:
                username = user['username'][:30]
            username = re.sub('[\W_]+', '', username)
            username = unidecode(username)
            gen_username = username[:30]

            # if email exists in database
            newemailfilter = EmailAdress.objects.filter(address=user['mail'])
            if (newemailfilter.count() == 1):
                username = newemailfilter.first().user.username
                newemail = newemailfilter.first()
            else:
                newemail = None

            newuser, created = ConflaUser.objects.get_or_create(username=username)

            if created or overwrite:
                if created:
                    newuser.password = "blank"

                newuser.gen_username = gen_username;
                newuser.first_name = user['name'][:30]
                if 'f_name' in user:
                    newuser.first_name = user['f_name'][:30]
                if 'l_name' in user:
                    newuser.last_name = user['l_name'][:30]
                if 'company' in user:
                    newuser.company = user['company']
                if 'position' in user:
                    newuser.position = user['position']
                if 'phone' in user:
                    newuser.phone = user['phone']
                if 'web' in user:
                    newuser.web = user['web']
                if 'github' in user:
                    newuser.github = user['github']
                if 'diaspora' in user:
                    newuser.diaspora = user['diaspora']
                if 'facebook' in user:
                    newuser.facebook = user['facebook']
                if 'twitter' in user:
                    newuser.twitter = user['twitter']
                if 'linkedin' in user:
                    newuser.linkedin = user['linkedin']
                if 'bio' in user:
                    newuser.bio = user['bio']

                # not in query set and not empty # FIXME should be valid email
                if (newemailfilter.count() == 0) and (user['mail']):
                    newemail = EmailAdress(user=newuser,address=user['mail'],is_active=False)
                    newemail.save()

                if newemail:
                    newuser.email = newemail.address;

                if user['avatar']:
                    try:
                        content = urllib.request.urlretrieve(user['avatar'])
                        ext = 'jpg'
                        newuser.picture.save(username + '.' + ext, File(open(content[0], 'rb')))
                        print("downloading " + user['avatar'])
                    except (urllib.error.HTTPError, urllib.error.URLError, http.client.BadStatusLine):
                        pass
                if overwrite and newuser.username in user_list:
                    users_modified += 1
                elif created:
                    user_list.append(newuser.username)
                    users_created += 1

                try:
                    newuser.full_clean()
                except ValidationError as e:
                    print(username)
                    print(str(e))
                    string = "ValidationError: " + username + " : " + str(e) + "<br/>\n"
                    for key in e.message_dict:
                        string = string + " " + user[key]
                    return '<div class="alert alert-warning import-alerts">'+ string + '</div>'


                newuser.save()


        # Generate sessions
        event_list = []
        collision_log = {}
        for event in json_obj['sessions']:
            setup_event = False
            events = Event.objects.filter(conf_id=conf, topic=event['topic'])
            if not events:
                # No existing event with given name, create one
                newevent = Event()
                newevent.conf_id = conf
                newevent.topic = event['topic']
                if 'description' in event:
                    newevent.description = event['description']
                if 'reqs' in event:
                    newevent.reqs = event['reqs'];
                if 'lang' in event:
                    newevent.lang = event['lang']
                if 'type' in event:
                    newevent.event_type = event['type']
                if 'notes' in event:
                    newevent.notes = event['notes']
                if 'slides' in event:
                    newevent.slides = event['slides']
                if 'video' in event:
                    newevent.video = event['video']
                if 'length' in event:
                    newevent.length = event['length']
                newevent.full_clean()
                newevent.save()
                events_created += 1
                event_list.append(newevent.topic)
            else:
                # One or more existing events
                if event['topic'] in event_list:
                    # The event has been added by this import
                    # Create another one
                    newevent = Event()
                    newevent.conf_id = conf
                    setup_event = True
                    events_created += 1
                else:
                    # Duplicate event already in the db
                    # If its a single one, we can modify it
                    if len(events) == 1:
                        newevent = events[0]

                    else:
                        # Mulitple events, no idea which to modify
                        # Log the collision
                        if event['topic'] in collision_log:
                            collision_log[event['topic']]['col_list'].append(event)
                        else:
                            collision_log[event['topic']] = { 'event_list' : events,
                                                              'col_list' : [event],}
                        events_collisions += 1
                        continue

                if setup_event or overwrite:
                    newevent.topic = event['topic']
                    if 'description' in event:
                        newevent.description = event['description']
                    if 'lang' in event:
                        newevent.lang = event['lang']
                    if 'type' in event:
                        newevent.event_type = event['type']
                    if 'notes' in event:
                        newevent.notes = event['notes']
                    if 'slides' in event:
                        newevent.slides = event['slides']
                    if 'video' in event:
                        newevent.video = event['video']
                    newevent.full_clean()
                    newevent.save()
                    if overwrite:
                        events_modified += 1
                else:
                    events_skipped += 1

            # Create rooms
            if 'room_short' in event:
                room, created = Room.objects.get_or_create(shortname=event['room_short'][:16])
                created, hr = HasRoom.objects.get_or_create(room=room, conference=conf, slot_length=3)

            setup_slot = False
            try:
                newslot = newevent.timeslot
            except ObjectDoesNotExist:
                # Create timeslot for the event
                newslot = Timeslot()
                newslot.conf_id = conf
                # New slot, we need to set it up properly
                setup_slot = True

            if 'event_start' in event and (setup_slot or setup_event or overwrite):
                newslot.room_id = room
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
                username = unidecode(username)
                gen_users = ConflaUser.objects.filter(gen_username=username)

                if len(gen_users) == 1:
                    newuser = gen_users[0]
                else:
                    newuser, created_speaker = ConflaUser.objects.get_or_create(username=username)
                    if created_speaker:
                        newuser.password = "blank"
                        newuser.first_name = speaker
                        newuser.full_clean()
                        newuser.save()
                        users_created += 1
                        user_list.append(newuser.username)
                newevent.speaker.add(newuser)

            tags = []
            # Create tags
            tag_idx = 0;
            for tag in event['tags']:
                tag = tag.strip()
                newtag, created = EventTag.objects.get_or_create(name=tag)
                newevent.tags.add(newtag)
                if tag_idx == 0:
                    newevent.prim_tag = newtag
                tag_idx = tag_idx + 1

            if 'track' in event:
                if event['track']: # and event['room_color']:
                    tag, created = EventTag.objects.get_or_create(name=event['track'])
                    tag.save()
                    newevent.prim_tag = EventTag.objects.get(name=event['track'])
            else:
                if len(tags) > 0:
                    tag = EventTag.objects.get(name=tags[0].strip())
                    newevent.prim_tag = tag

            newevent.save()   

        # Randomly color uncolored tags
        tags = EventTag.objects.filter(color__exact='').distinct()
        for tag in tags:
            r = lambda: (random.randint(0,255)+255) // 2
            tag.color = '#%02x%02x%02x' % (r(),r(),r())
            tag.save()

        # Setup start and end dates of the conference
        max_start = None
        max_end = None
        slots = Timeslot.objects.filter(conf_id=conf).order_by('start_time')

### FIXME find correct solution for issue #37
#        for slot in slots:
#            if not max_start:
#                max_start = slot.start_time.time()
#            elif max_start > slot.start_time.time():
#                max_start = slot.start_time.time()
#            if not max_end:
#                max_end = slot.end_time.time()
#            elif max_end < slot.end_time.time():
#                max_end = slot.end_time.time()
#        if max_start != None:
#            conf.start_time = max_start
#        if max_end != None:
#            conf.end_time = max_end
        if len(slots) > 0:
            conf.start_date = slots[0].start_time.date()
            conf.end_date = slots.reverse()[0].start_time.date()
        conf.save()

        return render(request, 'confla/admin/import_response.html',
                     { 'conf'      : conf,
                       'url_id' : url_id,
                       'users_created' : users_created,
                       'events_created' : events_created,
                       'users_modified' : users_modified,
                       'events_modified' : events_modified,
                       'users_skipped' : users_skipped,
                       'events_skipped' : events_skipped,
                       'events_collisions' : events_collisions,
                       'collision_log' : collision_log
                       })


class ExportView(generic.TemplateView):
    @permission_required('confla.can_organize', raise_exception=True)
    def export_view(request, url_id):
        template_name = 'confla/admin/export.html'
        conf = get_conf_or_404(url_id)

        return render(request, template_name,{ 'url_id' : url_id,
                            'conf_list' : Conference.objects.all().order_by('start_date'),
                            'conf' : conf,
        })

    def conf_list(request):
        result = {
            'conferences' : [],
            'timestamp' : '',
        }

        for conf in Conference.objects.filter(active=True).order_by("-start_date"):
            tz = timezone.get_default_timezone()
            rfc_time_format = "%a, %d %b %Y %X %z"

            start = ''
            end = ''
            start_rfc = ''
            end_rfc = ''
            url = request.build_absolute_uri(reverse('confla:splash', kwargs={'url_id' : conf.url_id}))
            url_json = request.build_absolute_uri(reverse('confla:export_mapp', kwargs={'url_id' : conf.url_id}))

            if conf.icon:
                icon = request.build_absolute_uri(conf.icon.url)
            else:
                icon = ''

            if conf.splash:
                splash = request.build_absolute_uri(conf.splash.url)
            else:
                splash = ''

            # Export conference information
            if conf.has_datetimes():
                start = datetime.combine(conf.start_date, conf.start_time).timestamp()
                start_rfc = datetime.combine(conf.start_date, conf.start_time).strftime(rfc_time_format)
                end = datetime.combine(conf.end_date, conf.end_time).timestamp()
                end_rfc = datetime.combine(conf.end_date, conf.end_time).strftime(rfc_time_format)

            if not StaticFilesStorage().exists('exports/' + conf.url_id + '.json'):
                # Need to generate the export
                ExportView.generate_json(request, conf.url_id)

            f = StaticFilesStorage().open('exports/' + conf.url_id + '.json', 'r')
            content = f.read()
            f.close()
            # Conference's export checksum
            conf_checksum = json.loads(content)['checksum']

            conf_dict = {    
                         'name' : conf.name,
                         'url_id': conf.url_id,
                         'url' : url,
                         'url_json' : url_json,
                         'url_feedback': 'http://python-conflab.rhcloud.com/feedback/{url_id}/{session_id}/', # this is template, the {url_id} and {session_id} should be replaced in client
                         'start' : start,
                         'end' : end,
                         'start_rfc' : start_rfc,
                         'end_rfc' : end_rfc,
                         'icon' : icon,
                         'splash' : splash,
                         'checksum': conf_checksum,
                         }
            result['conferences'].append(conf_dict)

        # Generate checksum
        result['checksum'] = hashlib.sha1(json.dumps(result).encode("utf-8")).hexdigest()



        return HttpResponse(json.dumps(result), content_type="application/json")



    def m_app(request, url_id):
        conf = get_conf_or_404(url_id)
        fn = conf.url_id + '.json'

        # FIXME file exists is not enough, it should be regenerated when user detail changes
        # Check if the export exists
#        if not StaticFilesStorage().exists('exports/' + fn):

        # Need to generate the export
        ExportView.generate_json(request, url_id)

        f = StaticFilesStorage().open('exports/' + fn, 'r')
        content = f.read()
        f.close()

        return HttpResponse(content, content_type="application/json")

    def generate_json(request, url_id):
        conf = get_conf_or_404(url_id)
        fn = conf.url_id + '.json'

        result = {}
        tz = timezone.get_default_timezone()
        rfc_time_format = "%a, %d %b %Y %X %z"

        start = ''
        end = ''

        # Export conference information
        if conf.has_datetimes():
            start = datetime.combine(conf.start_date, conf.start_time).timestamp()
            end = datetime.combine(conf.end_date, conf.end_time).timestamp()
        result['conference'] = { 'name' : conf.name,
                                 'id' : conf.url_id,
                                 'start' : start,
                                 'end' : end,
                                 }

        # Export events
        result['sessions'] = []
        slots = Timeslot.objects.filter(conf_id=conf)
        for slot in slots:
            if slot.room_id:
                event = slot.event_id
                session = {}
                session['session_id'] = event.pk
                session['lang'] = event.lang
                session['type'] = event.event_type
                # Primary tag color
                if event.prim_tag:
                    session['room_color'] = event.prim_tag.color 
                    session['track'] = event.prim_tag.name
                else:
                    session['room_color'] = '#787878'
                    session['track'] = ''
                session['room'] = slot.room_id.shortname
                session['room_short'] = slot.room_id.shortname
                session['speakers'] = [x.username for x in event.speaker.all()]
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
        for usr in ConflaUser.objects.filter(events__conf_id=conf, events__timeslot__isnull=False).distinct():
            user = {}
            user['username'] = usr.username
            user['name'] = usr.first_name + ' ' + usr.last_name
            user['f_name'] = usr.first_name
            user['l_name'] = usr.last_name
            user['position'] = usr.position
            user['company'] = usr.company
            user['joined'] = usr.date_joined.astimezone(tz).isoformat()[:19].replace('T', ' ')
            if usr.last_login:
                user['lastactive'] = usr.last_login.astimezone(tz).isoformat()[:19].replace('T', ' ')
            else:
                user['lastactive'] = ''
            if usr.picture:
                user['avatar'] = request.build_absolute_uri(usr.picture.url)
            else:
                user['avatar'] = ''
            user['web'] = usr.web
            user['facebook'] = usr.facebook
            user['twitter'] = usr.twitter
            user['linkedin'] = usr.linkedin
            user['github'] = usr.github
            user['diaspora'] = usr.diaspora

            user['phone'] = usr.phone
            user['mail'] = usr.email


            result['users'].append(user)

        # Export about
        # TODO: Proper about section once we have it
        result['about'] = [
            {
                'title' : 'About',
                'text'  : conf.about
            },
        ];
        for page in Page.objects.filter(conf_id=conf):
            result['about'].append(
                {
                    'title': page.title,
                    'text': page.abstract,
                }
            );

        # RSS
        result['rss'] = []

        if conf.gps:
            gps_position = conf.gps.split(',')

            result['places'] = [
                {
                    'name' : 'Venue',
                    'description' : conf.venue,
                    'icon' : '',
                    'lat' : gps_position[0],
                    'lon' : gps_position[1],
                },
                ]
        else:
            result['places'] = []

        for point in conf.geopoints.all():
            result['places'].append(
                {
                    'name' : point.name,
                    'description' : point.description,
                    'icon' : request.build_absolute_uri(point.icon.icon.url),
                    'lat' : point.latitude,
                    'lon' : point.longitude
                }
            )

        result['timestamp'] = int(datetime.now().strftime("%s"))

        # Generate checksum
        result['checksum'] = hashlib.sha1(json.dumps(result).encode("utf-8")).hexdigest()

        # Save the export into a file
        content = json.dumps(result)
        if StaticFilesStorage().exists('exports/' + fn):
            # File already exists
            f = StaticFilesStorage().open('exports/' + fn, 'w')
            f.write(content)
            f.close()
        else:
            # Need to create the file through the storage manager
            StaticFilesStorage().save('exports/' + fn, ContentFile(content))

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
                        if slot.get_start_datetime.strftime("%x %H:%M") == time['full']:
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
