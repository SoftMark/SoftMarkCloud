from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist

from soft_mark_cloud.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label

        self.fields['email'].widget.attrs['placeholder'] = 'Email'

    class Meta:
        model = User
        fields = ('username', 'email')

    def get_user(self):
        user = super(SignUpForm, self).save(commit=False)
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, label='Username/Email')
    password = forms.CharField(label='Password', strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            authenticated_user = authenticate(self.request, username=username, password=password)
            if not authenticated_user:
                try:
                    user = User.objects.get(email=username)
                    authenticated_user = authenticate(self.request, username=user.username, password=password)
                except ObjectDoesNotExist:
                    pass

            if not authenticated_user:
                raise self.get_invalid_login_error()

            self.confirm_login_allowed(authenticated_user)

        return self.cleaned_data
