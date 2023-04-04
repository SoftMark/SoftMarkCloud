from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework.decorators import api_view

from .forms import SignUpForm, LoginForm

from .models import User


@api_view(['GET'])
@login_required
def index(request):
    current_user = request.user
    return render(request, 'index.html', {'user': current_user})


@api_view(['GET', 'POST'])
@user_passes_test(lambda u: not u.is_authenticated, login_url='home')
def sign_up(request):
    if request.method == 'GET':
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})
    elif request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            user.save()
            login(request, user)
            # return redirect('home')
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
            # return render(request, 'signup.html', {'form': form})


@api_view(['GET', 'POST'])
@user_passes_test(lambda u: not u.is_authenticated, login_url='home')
def sign_in(request):
    if request.method == 'GET':
        form = LoginForm
        return render(request, 'signin.html', {'form': form})
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(username=username)
            except ObjectDoesNotExist:
                # If user does not exist with the username, try with the email
                try:
                    user = User.objects.get(email=username)
                except ObjectDoesNotExist:
                    # If user does not exist with the email as well, return an error
                    return JsonResponse({'errors': form.errors}, status=400)
                    # return render(request, 'signin.html', {'form': form, 'error': 'Incorrect login or password.'})
            if not user.check_password(password):
                # If password does not match, return an error
                return JsonResponse({'errors': form.errors}, status=400)
                # return render(request, 'signin.html', {'form': form, 'error': 'Incorrect login or password.'})
            login(request, user)
            return JsonResponse({'status': 'success'}, status=200)
            # return redirect('home')
        else:
            return JsonResponse({'errors': form.errors}, status=400)


@api_view(['GET'])
@login_required
def logout_user(request):
    logout(request)
    return redirect('home')
