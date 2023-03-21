import boto3

from soft_mark_cloud.cloud.core import Credentials, CloudClient


class AWSCredentials(Credentials):
    aws_access_key_id: str
    aws_secret_access_key: str


class AWSClient(CloudClient):
    def __init__(self, credentials: AWSCredentials, service_name: str):
        super().__init__(credentials)
        self._client = boto3.client(service_name, **self.credentials.__dict__)
