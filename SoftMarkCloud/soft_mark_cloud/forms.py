from django import forms
from django.contrib.auth.forms import UserCreationForm
from soft_mark_cloud.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def get_user(self):
        user = super(SignUpForm, self).save(commit=False)
        return user
