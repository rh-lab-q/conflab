from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext as _

from confla.models import ConflaUser

class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(max_length = 200,
                            widget = forms.PasswordInput())

    class Meta:
        model = ConflaUser
        fields = ['username','password', 'confirm_password', 'first_name', 'last_name', 'email', #'phone', 'company', 'position',
            # 'web', 'facebook', 'twitter', 'google_plus', 'linkedin',
            # 'bio'
            ]
        widgets = {
            'password' : forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

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
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if(commit):
            user.save()
        return user

class ProfileForm(forms.ModelForm):
        class Meta:
            model = ConflaUser
            fields = ['username', 'first_name',
                'last_name', 'email', 'phone', 'company', 'position',
                'web', 'facebook', 'twitter', 'google_plus', 'linkedin',
                'bio'
                ]
            widgets = {
                'password' : forms.PasswordInput(),
            }

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
