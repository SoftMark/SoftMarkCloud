from bson import ObjectId

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist

from soft_mark_cloud.models import User, AWSCredentials
from soft_mark_cloud.cloud.aws.core import AWSCreds
from soft_mark_cloud.cloud.aws.deploy.terraform import TerraformSettings


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

            self.user_cache = authenticated_user
            self.confirm_login_allowed(authenticated_user)

        return self.cleaned_data


class AWSCredentialsForm(forms.ModelForm):
    aws_access_key_id = forms.CharField(min_length=20, max_length=20, label='Access key id')
    aws_secret_access_key = forms.CharField(min_length=40, max_length=40, label='Secret Access key')

    class Meta:
        model = AWSCredentials
        fields = ['aws_access_key_id', 'aws_secret_access_key']


class TerraformSettingsForm(forms.Form):
    # TODO: add more regions
    region = forms.ChoiceField(
        choices=[('eu-central-1', 'Frankfurt (eu-central-1)'), ],
        widget=forms.Select(attrs={'class': 'my-select'}))

    # TODO: add more instance_types
    instance_type = forms.ChoiceField(
        choices=[('t2.micro', 't2.micro'), ],
        widget=forms.Select(attrs={'class': 'my-select'}))

    git_url = forms.CharField(label='Git url')
    manage_path = forms.CharField(label='Path to `manage.py` directory')
    requirements_path = forms.CharField(label='Path to `requirements.txt` file')

    def gen(self, creds: AWSCreds) -> TerraformSettings:
        """
        Generates TerraformSettings instance from TerraformSettingsForm cleaned data
        """
        return TerraformSettings(
            creds=creds,
            resource_name="instance-" + ObjectId().__str__(),
            **self.cleaned_data)
