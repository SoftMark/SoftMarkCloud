import boto3
from dataclasses import dataclass
from typing import List

from botocore.exceptions import ClientError

from soft_mark_cloud.cloud.core import Credentials, CloudClient


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
    def from_model_to_data(cls, model) -> 'AWSCreds':
        return cls(
            aws_access_key_id=model.aws_access_key_id,
            aws_secret_access_key=model.aws_secret_access_key)


class STSClient(CloudClient):
    """
    Client that allows manage authorisation and access to various resources.
    """
    service_name = 'sts'

    def __init__(self, credentials: AWSCreds):
        super().__init__(credentials)
        self.boto3_client = boto3.client(self.service_name, **self.credentials.__dict__)

    def validate_credentials(self) -> bool or tuple[bool, str]:
        """
        Check credentials
        """
        try:
            self.boto3_client.get_caller_identity()
            return True, 'Credentials are valid'
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return False, f"{error_code}: {error_message}"


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
