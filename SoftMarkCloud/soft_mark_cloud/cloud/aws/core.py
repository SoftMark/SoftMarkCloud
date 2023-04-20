import boto3
from dataclasses import dataclass
from typing import List

from soft_mark_cloud.cloud.core import Credentials, CloudClient


@dataclass
class AWSResource:
    """
    AWS resource dataclass
    """
    arn: str
    resource_type_: str

    @property
    def json(self):
        return self.__dict__


@dataclass
class AWSCreds(Credentials):
    """
    Credentials holder dataclass
    """
    aws_access_key_id: str
    aws_secret_access_key: str


class AWSClient(CloudClient):
    """
    AWS client abstract class
    """
    service_name = None

    def __init__(self, credentials: AWSCreds, **kwargs):
        super().__init__(credentials)
        self.boto3_client = boto3.client(self.service_name, **self.credentials.__dict__, **kwargs)
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
        raise NotImplementedError('Can`t call abstract method collect_resources')

    def collect_all(self):
        """
        Base collect all method
        """
        return {
            self.service_name: [i.json for i in self.collect_resources()]}


class AWSGlobalClient(AWSClient):
    """
    Global AWS client abstract class
    """
    def __init__(self, credentials: AWSCreds):
        super().__init__(credentials)


class AWSRegionalClient(AWSClient):
    """
    Regional AWS client abstract class
    """
    def __init__(self, credentials: AWSCreds, region_name: str):
        self.region_name = region_name
        super().__init__(credentials, region_name=region_name)
