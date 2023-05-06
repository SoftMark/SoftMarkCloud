import time
from typing import Any

from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from soft_mark_cloud.cloud.aws import AWSCreds
from soft_mark_cloud.cloud.aws.cache import AWSCache
from soft_mark_cloud.cloud.aws.collector import AWSCollector
from soft_mark_cloud.cloud.aws.status import AWSStatusDao

from soft_mark_cloud.forms import SignUpForm, LoginForm, AWSCredentialsForm
from soft_mark_cloud.models import AWSCredentials


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


@api_view(['GET', 'POST', 'DELETE'])
@login_required
def account_manager(request):
    current_user = request.user
    try:
        creds = AWSCredentials.objects.get(user=current_user)
    except ObjectDoesNotExist:
        creds = None

    if request.method == 'GET':
        if creds:
            creds = AWSCreds.from_model(creds)
            if creds.is_valid:
                resp = {'status': 200, 'creds': creds, 'form': AWSCredentialsForm()}
            else:
                resp = {'status': 403, 'error': 'Ineffective AWS credentials', 'creds': creds}
        else:
            resp = {'status': 404, 'form': AWSCredentialsForm()}

    elif request.method == 'POST':
        if creds:
            resp = {'status': 200, 'creds': creds, 'form': AWSCredentialsForm()}
        else:
            form = AWSCredentialsForm(request.POST)
            if form.is_valid():
                creds_form = form.instance
                creds = AWSCreds.from_model(creds_form)
                if creds.is_valid:
                    creds_form.user = current_user
                    creds_form.save()
                    resp = {'status': 200, 'creds': creds}
                else:
                    resp = {'status': 401, 'form': form, 'error': 'Ineffective AWS credentials'}
            else:
                resp = {'status': 404, 'form': form}

    else:  # request.method == 'DELETE':
        if creds:
            creds.delete()

        AWSCache.clear_cache(request.user)
        resp = {'status': 404, 'form': AWSCredentialsForm()}

    return render(request, 'account_manager.html', resp)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cloud_view(request):
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
    def _check_refreshing():
        if refresh_status := AWSStatusDao.get_status(request.user, AWSCollector.process_name):
            return not refresh_status.done
        else:
            return False

    def _render(resp: Any, status_code: int, refreshing_: bool = False):
        return render(request, 'cloud_view.html',
                      {
                          'response': response,
                          'status': status_code,
                          'refreshing': refreshing_
                      })

    try:
        creds_db = AWSCredentials.objects.get(user=request.user)
    except ObjectDoesNotExist:
        response, status = 'AWS credentials not provided', 401
        return _render(response, status)

    creds = AWSCreds.from_model(creds_db)
    if not creds.is_valid:
        response, status = 'Ineffective AWS credentials', 403
        return _render(response, status)

    if 'refresh' in request.GET and not _check_refreshing():
        AWSCollector(credentials=creds).run_async(user=request.user)
        time.sleep(1)  # Let update refresh status
        return redirect('cloud_view')

    aws_data = AWSCache.get_cache_data_json(request.user)
    response, status, refreshing = aws_data, 200, _check_refreshing()

    return _render(response, status, refreshing)
