from pytz import common_timezones as tzs

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext as _
from captcha.fields import CaptchaField

from confla.models import Event, Conference, Room, ConflaUser, Paper, EmailAdress, Page

class ImportFileForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ImportFileForm, self).__init__(*args, **kwargs)
        self.fields['overwrite'].label = "Overwrite existing?"

    file = forms.FileField()
    overwrite = forms.BooleanField(required=False)

class ConfCreateForm(forms.ModelForm):

    class Meta:
        model = Conference
        choices = (('5', '5'),('10', '10'),('15', '15'),('20', '20'), ('25', '25'),('30', '30'),('45', '45'),('60', '60'),)
        fields = ['name', 'start_date', 'end_date', 'cfp_start', 'cfp_end', 'start_time',
            'end_time', 'rooms', 'url_id', 'timedelta', 'active', 'active_schedule',
            'about', 'venue', 'gps', 'web', 'facebook', 'twitter', 'google_plus', 'linkedin', 'youtube', 'slideshare', 'splash', 'icon', 'timezone', ]
        timezones = [(x,x) for x in tzs]
        timezones.insert(0, ('',''))

        widgets = {
            'timedelta' : forms.Select(choices=choices),
            'timezone' : forms.Select(choices=timezones),
        }

    def __init__(self, *args, **kwargs):
        super(ConfCreateForm, self).__init__(*args, **kwargs)

        classes = 'form-control input-sm'
        for key in self.fields.keys():
            if key not in ['splash', 'icon', 'active', 'active_schedule']:
                self.fields[key].widget.attrs.update({'class' : classes})

        for key in ['name', 'url_id']:
            self.fields[key].widget.attrs.update({'required' : 'true'})
        self.fields['rooms'].widget.attrs.update({'class' : 'form-control input-sm selectized-input',})

class RoomCreateForm(forms.ModelForm):

    class Meta:
        model = Room
        fields = ['shortname', 'description', 'color']

    def __init__(self, *args, **kwargs):
        super(RoomCreateForm, self).__init__(*args, **kwargs)

        for key in self.fields.keys():
            self.fields[key].widget.attrs.update({'class' : 'form-control input-sm'})

class EventCreateForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['topic', 'description', 'speaker', 'tags', 'notes']


    def __init__(self, *args, **kwargs):
        super(EventCreateForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                            'style' : 'width: 100%',
                            'class' : 'form-control input-sm'
            })
        self.fields['topic'].widget.attrs.update({'placeholder' : _('Topic')})
        self.fields['description'].widget.attrs.update({'rows' : '5',
                                                        'placeholder' : _('Description')})
        self.fields['notes'].widget.attrs.update({'rows' : '5',
                                                        'placeholder' : _('Notes')})
        self.fields['speaker'].widget.attrs.update({'class' : 'sel-speaker selectized-input',
                                                    'style': 'visibility:hidden'})
        self.fields['tags'].widget.attrs.update({'class' : 'sel-tag selectized-input',
                                                    'style': 'visibility:hidden'})
class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['topic', 'description', 'lang', 'slides', 'video',
                  'google_doc_url', 'speaker', 'tags', 'prim_tag']

    def __init__(self, *args, **kwargs):
        super(EventEditForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                            'class' : 'form-control input-sm'
            })

class EventFullEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [ 'topic', 'description', 'event_type', 'lang', 'slides', 'video', 'google_doc_url', 'speaker', 'tags', 'prim_tag', 'notes', 'reqs' ]

    def __init__(self, *args, **kwargs):
        super(EventFullEditForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                            'class' : 'form-control input-sm'
            })

class ResetPasswordForm(forms.ModelForm):
    class Meta:
        model = ConflaUser
        fields = ['email']



class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(max_length = 200,
                            widget = forms.PasswordInput())
    captcha = CaptchaField()
    error_css_class = 'has-error'
    success_css_class = 'has-success'

    class Meta:
        model = ConflaUser
        fields = ['username','password', 'confirm_password', 'captcha',
            'email', 'first_name', 'last_name',
            ]
        widgets = {
            'password' : forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

        for key in self.fields.keys():
            self.fields[key].widget.attrs.update({'class' : 'form-control input-sm'})

        self.fields['email'].required = True
        self.fields['confirm_password'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_confirm_password(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('confirm_password')

        if not(password2):
            raise forms.ValidationError("Password confirmation is required.")

        if password1 != password2:
            raise forms.ValidationError("The passwords do not match.")

        return password2

    def save(self, commit=True):
        """
        Overrides the default save() method so that it stores the password in
        hashed form.
        """
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if(commit):
            user.save()
        return user

class EmailForm(forms.ModelForm):
    class Meta:
        model = EmailAdress
        fields = ['address']

    def __init__(self, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)

class PaperForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = ['title', 'abstract']

    def __init__(self, *args, **kwargs):
        super(PaperForm, self).__init__(*args, **kwargs)

        for key in self.fields.keys():
            if key == 'source':
                continue;
            self.fields[key].widget.attrs.update({'class' : 'form-control input-sm'})

class ProfileForm(forms.ModelForm):
    class Meta:
        model = ConflaUser
        fields = ['first_name', 'last_name', 'phone',
                  'company', 'position', 'web', 'facebook',
                  'twitter', 'google_plus', 'linkedin', 'github', 'bio',
                  'picture',
            ]
        widgets = {
            'password' : forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        for key in self.fields.keys():
            if key not in ['picture']:
                self.fields[key].widget.attrs.update({'class' : 'form-control input-sm'})

class AuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': _('Username'),
                                                     'class' : 'form-control',
                                                     'required' : 'required',
                                                     'autofocus' : 'autofocus',
        })
        self.fields['password'].widget.attrs.update({'placeholder': _('Password'),
                                                     'class' : 'form-control',
                                                     'required' : 'required',
        })

class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title', 'abstract']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({
                            'class' : 'form-control input-sm'
            })
