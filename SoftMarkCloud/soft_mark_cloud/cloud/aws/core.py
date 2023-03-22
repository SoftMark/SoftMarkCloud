import boto3
from dataclasses import dataclass

from soft_mark_cloud.cloud.core import Credentials, CloudClient


@dataclass
class AWSCredentials(Credentials):
    """
    Credentials holder dataclass
    """
    aws_access_key_id: str
    aws_secret_access_key: str


class AWSGlobalClient(CloudClient):
    """
    Global AWS client class
    """
    def __init__(self, credentials: AWSCredentials, service_name: str):
        super().__init__(credentials)
        self.client = boto3.client(service_name, **self.credentials.__dict__)


class AWSRegionalClient(CloudClient):
    """
    Regional AWS client class
    """
    all_regions = 'eu-central-1',  # TODO: add more regions

    def __init__(self, credentials: AWSCredentials, service_name: str, region_name: str):
        super().__init__(credentials)
        self.client = boto3.client(service_name, region_name=region_name, **self.credentials.__dict__)
