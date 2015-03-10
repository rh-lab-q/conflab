from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.hashers import check_password 
from django.core.urlresolvers import reverse

from confla.models import User

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class ScheduleView(generic.TemplateView):
    template_name = 'confla/schedule.html'

class LoginView(generic.TemplateView):
    template_name = 'confla/login.html'
    #TODO: OpenSSL,  or some other crypto for POST
    def check_login(request):
        if request.method == "POST":
            try:    
                user = User.objects.get(pk=request.POST['login'])
                if check_password(request.POST['password'], user.password):
                    request.session['user'] = user.username
                else:
                    raise User.DoesNotExist
            except (KeyError, User.DoesNotExist):
                return render(request, 'confla/login.html', {
                                 'error_message': "Wrong username/password."})
            else:
                return HttpResponseRedirect(reverse('confla:users'))
        else:
            return HttpResponseRedirect(reverse('confla:login')) 

class UserView(generic.TemplateView):
    template_name = 'confla/base.html'
