from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from soft_mark_cloud.cloud.aws import AWSCreds
from soft_mark_cloud.cloud.aws.collector import AWSCollector
from soft_mark_cloud.forms import SignUpForm, LoginForm
from soft_mark_cloud.models import AWSCredentials


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def aws_cloud_data(request):
    """
    Echo request

    Returns
    -------
    Out:
        Response the same as request

    Examples
    --------
    >>> import requests
    >>> requests.get(
    ...     url='http://127.0.0.1:8000/api/cloud_data',
    ...     headers={'Authorization': 'Token db18760656b95b62dfaa788975ab67dd8c062562'}
    ... )
    Out:
    <Response [200]>
    """
    try:
        creds_db = AWSCredentials.objects.get(user=request.user)
    except ObjectDoesNotExist:
        return Response('AWS credentials not provided', status=401)

    creds = AWSCreds(
        aws_access_key_id=creds_db.aws_access_key_id,
        aws_secret_access_key=creds_db.aws_secret_access_key)

    collector = AWSCollector(credentials=creds)
    aws_data = collector.collect_all()
    return Response(aws_data, status=200)


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
        form = LoginForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)


@api_view(['GET'])
@login_required
def logout_user(request):
    logout(request)
    return redirect('home')
