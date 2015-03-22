from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from confla.models import ConflaUser
from confla.forms import RegisterForm, ProfileForm, AuthForm

class AboutView(generic.TemplateView):
    template_name = 'confla/about.html'

class ScheduleView(generic.TemplateView):
    template_name = 'confla/schedule.html'

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

        return render(request, 'confla/profile.html',{
            'form' : form,
            })

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
