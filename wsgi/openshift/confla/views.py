import json

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from confla.models import ConflaUser, Conference, Room, Timeslot, EmailAdress
from confla.forms import *

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class VolunteerView(generic.TemplateView):
    template_name = 'confla/volunteer.html'

    @permission_required('confla.can_volunteer', raise_exception=True)
    def my_view(request):
        return render(request, VolunteerView.template_name)


class ScheduleView(generic.TemplateView):
    template_name = 'confla/schedule.html'

    def my_view(request):
        #TODO: Need to make proper conference getter
        conf = Conference.objects.all()[0]
        return render(request, ScheduleView.template_name,
                       { 'time_list' : conf.get_delta_list(),
                         'room_list' : conf.rooms.all(),
                         'slot_list' : Timeslot.objects.filter(conf_id=conf.id),
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
            except ValidationError as e:
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

class TimetableView(generic.TemplateView):
    template_name = "confla/timetable.html"

    @permission_required('confla.can_organize', raise_exception=True)
    def view_timetable(request):
        #TODO: Needs certain permissions to be displayed
        conf = Conference.objects.all()[0]
        return render(request, TimetableView.template_name,
                       { 'time_list' : conf.get_delta_list(),
                         'room_list' : Room.objects.all(),
                         'slot_list' : Timeslot.objects.filter(conf_id=conf.id),
                    })

    def json_to_timetable(request):
       pass
