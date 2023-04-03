import boto3
from dataclasses import dataclass
from logging import getLogger
from typing import List

from soft_mark_cloud.cloud.core import Credentials, CloudClient


log = getLogger("AWSLogger")


@dataclass
class AWSResource:
    """
    AWS resource dataclass
    """
    arn: str

    @property
    def json(self):
        return self.__dict__


@dataclass
class AWSCredentials(Credentials):
    """
    Credentials holder dataclass
    """
    aws_access_key_id: str
    aws_secret_access_key: str


class AWSClient(CloudClient):
    """
    AWS client class
    """
    # TODO: Make `service_name` as class field
    def __init__(self, credentials: AWSCredentials, service_name: str, **kwargs):
        super().__init__(credentials)
        self.service_name = service_name
        self.boto3_client = boto3.client(service_name, **self.credentials.__dict__, **kwargs)
        self.account_id = self.get_account_id()

    @property
    def sts_client(self):
        return boto3.client('sts', **self.credentials.__dict__)

    def get_account_id(self) -> str:
        return self.sts_client.get_caller_identity()['Account']

    def collect_resources(self) -> List[AWSResource]:
        """
        Abstract collect all resources method
        """
        # TODO: raise error if not implemented
        log.warning("Warning. Collecting is not Implemented!")
        return []

    def collect_all(self):
        """
        Base collect all method
        """
        return {
            self.service_name: {
                i.arn: i.json for i in self.collect_resources()}}


class AWSGlobalClient(AWSClient):
    """
    Global AWS client class
    """
    def __init__(self, credentials: AWSCredentials, service_name: str):
        super().__init__(credentials, service_name)


class AWSRegionalClient(AWSClient):
    """
    Regional AWS client class
    """
    def __init__(self, credentials: AWSCredentials, service_name: str, region_name: str):
        self.region = region_name
        super().__init__(credentials, service_name, region_name=region_name)
