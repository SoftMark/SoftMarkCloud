import time
from typing import Any

from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from soft_mark_cloud.cloud.aws import AWSCreds
from soft_mark_cloud.cloud.aws.cache import AWSCache
from soft_mark_cloud.cloud.aws.collector import AWSCollector
from soft_mark_cloud.cloud.aws.status import AWSStatusDao
from soft_mark_cloud.cloud.aws.deploy.terraform import AWSDeployer

from soft_mark_cloud.forms import SignUpForm, LoginForm, AWSCredentialsForm, TerraformSettingsForm
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
        AWSStatusDao.delete_status(request.user, AWSCollector.process_name)
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
    REFRESH_TIME_LIMIT = 180  # 3 minutes

    def _check_refreshing():
        if refresh_status_ := AWSStatusDao.get_status(request.user, AWSCollector.process_name):
            refresh_status_ = AWSStatusDao.check_expired(refresh_status_, REFRESH_TIME_LIMIT)
            return not (refresh_status_.failed or refresh_status_.done)
        return False

    def _render(
            resp: Any, status_code: int, refreshing_: bool = False, failed_: bool = False, done_: bool = False,
            started_at: datetime = None
    ):
        if started_at:
            started_at = started_at.strftime("%d-%m-%Y %H:%M:%S UTC")
        return render(request, 'cloud_view.html',
                      {
                          'response': response,
                          'status': status_code,
                          'refreshing': refreshing_,
                          'failed': failed_,
                          'done': done_,
                          'started_at': started_at
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

    refreshing = _check_refreshing()
    if 'refresh' in request.GET and not refreshing:
        AWSCollector(credentials=creds).run_async(user=request.user)
        time.sleep(2)  # Let update refresh status
        return redirect('cloud_view')

    aws_data = AWSCache.get_cache_data(request.user) or AWSCollector.empty_data
    response, status = aws_data, 200

    refresh_status = AWSStatusDao.get_status(request.user, AWSCollector.process_name)

    kwargs = {}
    if refresh_status:
        kwargs.update({
            'failed_': refresh_status.failed, 'done_': refresh_status.done, 'started_at': refresh_status.created_at})

    return _render(
        response, status, refreshing, **kwargs)


@api_view(['GET', 'POST', 'DELETE'])
@login_required
def deployer(request):
    DEPLOY_TIME_LIMIT = 600  # 10 minutes
    user = request.user

    try:
        creds = AWSCreds.from_model(
            model_instance=AWSCredentials.objects.get(user=user))
    except ObjectDoesNotExist:
        resp = {'status': 401, 'error_msg': "AWS credentials not provided"}
        return render(request, 'deployer.html', resp)

    deploy_status = AWSStatusDao.get_status(user, AWSDeployer.process_name)
    if request.method == 'GET':
        if not deploy_status:
            resp = {'status': 204, 'form': TerraformSettingsForm()}
        else:
            deploy_status = AWSStatusDao.check_expired(deploy_status, DEPLOY_TIME_LIMIT)
            resp = {'status': 200, 'deploy_details': deploy_status.details, 'expired': deploy_status.failed}

    elif request.method == 'POST':
        if deploy_status:
            return redirect('deployer')

        form = TerraformSettingsForm(request.POST)
        if form.is_valid():
            settings = form.gen(creds)
            AWSDeployer(settings).deploy_async(user)
            time.sleep(3)  # Let update deploy status
            return redirect('deployer')
        else:
            resp = {'status': 204, 'form': form}

    else:  # request.method == 'DELETE':
        if deploy_status and (deploy_status.done or deploy_status.failed):
            AWSStatusDao.delete_status(user, AWSDeployer.process_name)
        return redirect('deployer')

    return render(request, 'deployer.html', resp)
