import boto3
from botocore.exceptions import ClientError

from dataclasses import dataclass
from typing import List

from soft_mark_cloud.cloud.core import Credentials, CloudClient
from soft_mark_cloud.models import AWSCredentials


@dataclass
class AWSResource:
    """
    AWS resource dataclass
    """
    arn: str

    @property
    def resource_type(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def json(self):
        data = self.__dict__
        data['resource_type'] = self.resource_type
        return data


@dataclass
class AWSCreds(Credentials):
    """
    Credentials holder dataclass
    """
    aws_access_key_id: str
    aws_secret_access_key: str

    @classmethod
    def from_model(cls, model_instance: 'AWSCredentials') -> 'AWSCreds':
        """
        Generates `AWSCreds` instance
        """
        return cls(
            aws_access_key_id=model_instance.aws_access_key_id,
            aws_secret_access_key=model_instance.aws_secret_access_key)

    @property
    def is_valid(self) -> bool:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        try:
            sts_client.get_caller_identity()
            return True
        except ClientError:
            return False

    def get_account_id(self):
        sts_client = boto3.client('sts', **self.__dict__)
        return sts_client.get_caller_identity()['Account']


class AWSClient(CloudClient):
    """
    AWS client abstract class
    """
    service_name = None

    def __init__(self, credentials: AWSCreds, **kwargs):
        super().__init__(credentials)
        self.boto3_client = boto3.client(self.service_name, **self.credentials.__dict__, **kwargs)
        self.account_id = credentials.get_account_id()

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
