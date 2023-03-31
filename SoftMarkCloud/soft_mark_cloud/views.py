from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist

from .forms import SignUpForm

from models import User


def sign_up(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')

            # Check for uniqueness of email and username
            if User.objects.filter(email=email).exists():
                form.add_error('email', 'User with this email already exists')
            elif User.objects.filter(username=username).exists():
                form.add_error('username', 'User with this username already exists')
            else:
                user.save()
                login(request, user)
                return redirect('index.html')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {
        'form': form,
    })


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
