from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from soft_mark_cloud.models import AWSCredentials
from soft_mark_cloud.cloud.aws import AWSCreds
from soft_mark_cloud.cloud.aws.collector import AWSCollector


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
