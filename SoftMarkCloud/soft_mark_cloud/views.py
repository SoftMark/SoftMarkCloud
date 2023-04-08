from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework.decorators import api_view
from .forms import SignUpForm, LoginForm


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
            return redirect('home')
        else:
            return render(request, 'signup.html', {'form': form})


@api_view(['GET', 'POST'])
@user_passes_test(lambda u: not u.is_authenticated, login_url='home')
def sign_in(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'signin.html', {'form': form})


@api_view(['GET'])
@login_required
def logout_user(request):
    logout(request)
    return redirect('home')
