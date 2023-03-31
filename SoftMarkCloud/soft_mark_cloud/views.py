from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from django.http import JsonResponse

from .forms import SignUpForm

from .models import User


def index(request):
    return render(request, 'index.html')


@api_view(['GET', 'POST'])
def sign_up(request):
    if request.method == 'GET':
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})
    elif request.method == 'POST':
        form = SignUpForm(request.data)
        if form.is_valid():
            user = form.get_user()
            user.save()
            login(request, user)
            return redirect('index')
        else:
            return JsonResponse({'errors': form.errors}, status=400)


def sign_in(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get data from the form
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Try to authenticate the user using username
            user = authenticate(username=username_or_email, password=password)
            if user is None:
                # If authentication failed, try by email
                try:
                    user = User.objects.get(email=username_or_email)
                    user = authenticate(username=user.username, password=password)
                except ObjectDoesNotExist:
                    # Error handling - user not found in database
                    messages.error(request, 'Incorrect login or password')
                    return render(request, 'signin.html')
            if user is not None:
                login(request, user)
                return redirect('index.html')
            else:
                form.add_error(None, 'Incorrect login or password')
    else:
        form = AuthenticationForm
        return render(request, 'signin.html', {
            'form': form,
        })


def sign_out(request):
    logout(request)
    return redirect('index.html')
