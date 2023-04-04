from django import forms
from django.contrib.auth.forms import UserCreationForm
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


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
