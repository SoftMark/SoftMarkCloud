import datetime
from dataclasses import dataclass
from typing import Iterator, List

from soft_mark_cloud.cloud.aws.core import AWSRegionalClient, AWSCredentials, AWSResource


@dataclass
class EC2Instance(AWSResource):
    """
    EC2 Instance dataclass
    """
    instance_id: str
    instance_type: str
    instance_state: str
    subnet_id: str
    launch_time: datetime.datetime

    @classmethod
    def from_api_dict(cls, data: dict) -> 'EC2Instance':
        return cls(
            arn=data['InstanceArn'],
            instance_id=data['InstanceId'],
            instance_type=data['InstanceType'],
            instance_state=data['State']['Name'],
            subnet_id=data['SubnetId'],
            launch_time=data['LaunchTime'])


class EC2Client(AWSRegionalClient):
    """
    This class provides EC2 API functional
    """

    def __init__(self, credentials: AWSCredentials, region_name: str):
        super().__init__(credentials, region_name=region_name, service_name='ec2')

    def gen_ec2_arn(self, instance_id: str) -> str:
        """
        Example: arn:aws:ec2:us-east-1:123456789012:instance/i-012abcd34efghi56
        """
        return f'arn:aws:ec2:{self.region}:{self.account_id}:instance/{instance_id}'

    # TODO: fetch more EC2 instances data
    def describe_ec2_instances(self) -> Iterator[EC2Instance]:
        """
        Collects ec2 instances for client region

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.services.ec2 import AWSCredentials, EC2Client
        ... creds = AWSCredentials(
        ...     aws_access_key_id='{aws_access_key_id}',
        ...     aws_secret_access_key='{aws_secret_access_key}'
        ... )
        ... client = EC2Client(credentials=creds, region_name='{region_name}')
        ... ec2_instances = list(client.describe_ec2_instances())
        ... print(ec2_instances)
        out:
            List of EC2Instance class instances.
        """
        resp: dict = self.boto3_client.describe_instances()
        for reservation_data in resp.get('Reservations', []):
            for instance_data in reservation_data.get('Instances'):
                instance_arn = self.gen_ec2_arn(instance_data['InstanceId'])
                instance_data['InstanceArn'] = instance_arn
                yield EC2Instance.from_api_dict(instance_data)

    def collect_resources(self) -> List[EC2Instance]:
        return list(self.describe_ec2_instances())
