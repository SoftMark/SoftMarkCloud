import datetime
from dataclasses import dataclass
from typing import Iterator

from soft_mark_cloud.cloud.aws.core import AWSClient, AWSCredentials


@dataclass
class EC2Instance:
    instance_id: str
    instance_type: str
    subnet_id: str
    launch_time: datetime.datetime

    @classmethod
    def from_api_dict(cls, data: dict) -> 'EC2Instance':
        return cls(
            instance_id=data['InstanceId'],
            instance_type=data['InstanceType'],
            subnet_id=data['SubnetId'],
            launch_time=data['LaunchTime']
        )


class EC2Client(AWSClient):
    """
    This class provides EC2 api functional

    Examples
    --------
    >>> from from soft_mark_cloud.cloud.aws.services.ec2 import AWSCredentials, EC2Client
    ... creds = AWSCredentials(
    ...     aws_access_key_id='{aws_access_key_id}',
    ...     aws_secret_access_key='{aws_secret_access_key}'
    ... )
    ... client = EC2Client(credentials=creds, region_name='{region_name}')
    ... list(client.describe_ec2_instances())
    out:
        List of EC2Instance class instances.
    """

    def __init__(self, credentials: AWSCredentials, region_name: str):
        super().__init__(credentials, region_name=region_name, service_name='ec2')

    def describe_ec2_instances(self) -> Iterator[EC2Instance]:
        """
        Collects ec2 instances
        """
        resp: dict = self.client.describe_instances()
        for reservation_data in resp.get('Reservations', []):
            for instance_data in reservation_data.get('Instances'):
                yield EC2Instance.from_api_dict(instance_data)
