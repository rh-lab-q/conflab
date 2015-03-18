from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.hashers import check_password, make_password
from django.core.urlresolvers import reverse

from confla.models import ConflaUser
from confla.forms import RegisterForm

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class ScheduleView(generic.TemplateView):
    template_name = 'confla/schedule.html'

class LoginView(generic.TemplateView):
    template_name = 'confla/login.html'
    #TODO: OpenSSL,  or some other crypto for POST
    def check_login(request):
        if not(request.method == "POST"):
            return HttpResponseRedirect(reverse('confla:login'))
        try:
            user = ConflaUser.objects.get(username=request.POST['login'])
            if check_password(request.POST['password'], user.password):
                request.session['user'] = user.username
            else:
                raise ConflaUser.DoesNotExist
        except (KeyError, ConflaUser.DoesNotExist):
            return render(request, 'confla/login.html', {
                         'error_message': "Wrong username/password."})
        else:
            return HttpResponseRedirect(reverse('confla:users'))

    def logout(request):
        try:
            del request.session['user']
        except KeyError:
            pass
        return HttpResponseRedirect(reverse('confla:login'))


class UserView(generic.TemplateView):
    template_name = 'confla/base.html'

class RegisterView(generic.TemplateView):
    template_name = 'confla/thanks.html'

    def user_register(request):
        if request.method == 'POST': # the form was submitted
            form = RegisterForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('confla:thanks'))
        else:
            form = RegisterForm()

        return render(request, 'confla/register.html', {
            'form' : form,
        })
