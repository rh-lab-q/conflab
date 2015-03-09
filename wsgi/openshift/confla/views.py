from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.hashers import check_password 

from confla.models import User

def check_psswd(request, username, password):
    user = get_object_or_404(User, pk=username)
    if check_password(password, user.password):
        request.session['user'] = username
        return HttpResponse("Welcome user %s." % username)
    else:
        return HttpResponse("Wrong Password %s" % password)

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class ScheduleView(generic.TemplateView):
    template_name = 'confla/schedule.html'

class LoginView(generic.TemplateView):
    template_name = 'confla/login.html'

class UserView(generic.TemplateView):
    template_name = 'confla/base.html'
