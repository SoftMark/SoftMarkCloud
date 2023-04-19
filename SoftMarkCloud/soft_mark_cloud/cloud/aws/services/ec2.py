import datetime
from dataclasses import dataclass, field
from typing import Iterator, List, Dict

from soft_mark_cloud.cloud.aws.core import AWSRegionalClient, AWSCreds, AWSResource


@dataclass
class EC2Instance(AWSResource):
    """
    EC2 Instance dataclass
    """
    instance_id: str
    instance_type: str
    instance_state: str
    subnet_id: str
    vpc_id: str
    launch_time: datetime.datetime

    @classmethod
    def from_api_dict(cls, data: dict) -> 'EC2Instance':
        return cls(
            arn=data['InstanceArn'],
            resource_type='ec2_instance',
            instance_id=data['InstanceId'],
            instance_type=data['InstanceType'],
            instance_state=data['State']['Name'],
            subnet_id=data['SubnetId'],
            vpc_id=data['VpcId'],
            launch_time=data['LaunchTime'])

    @property
    def json(self):
        data = self.__dict__
        data['launch_time'] = self.launch_time.isoformat()
        return data


@dataclass
class Subnet(AWSResource):
    vpc_id: str
    subnet_id: str
    availability_zone: str
    ec2_instance: EC2Instance = field(default_factory=dict)

    @classmethod
    def from_api_dict(cls, subnet: dict) -> 'Subnet':
        return cls(
            arn=subnet['Arn'],
            resource_type='subnet',
            vpc_id=subnet['VpcId'],
            subnet_id=subnet['SubnetId'],
            availability_zone=subnet['AvailabilityZone']
        )


@dataclass
class VPC(AWSResource):
    """
    VPC Instance dataclass
    """
    id: str
    is_default: bool
    state: str
    subnets: List[Subnet]

    @classmethod
    def from_api_dict(cls, vpc: dict) -> 'VPC':
        return cls(
            arn=vpc['Arn'],
            resource_type='vpc',
            id=vpc['VpcId'],
            is_default=vpc['IsDefault'],
            state=vpc['State'],
            subnets=vpc['Subnets'])


class EC2Client(AWSRegionalClient):
    """
    This class provides EC2 API functional
    """
    service_name = 'ec2'

    def __init__(self, credentials: AWSCreds, region_name: str):
        super().__init__(credentials, region_name=region_name)

    def generate_ec2_arn(self, instance_id: str) -> str:
        """
        Example: arn:aws:ec2:us-east-1:123456789012:instance/i-012abcd34efghi56
        """
        return f'arn:aws:ec2:{self.region_name}:{self.account_id}:instance/{instance_id}'

    def generate_vpc_arn(self, vpc_id: str) -> str:
        """
        Example:
            arn:aws:ec2:us-east-1:123456789012:vpc/vpc-1234567890abcdef0
        """
        return f'arn:aws:ec2:{self.region_name}:{self.account_id}:vpc/{vpc_id}'

    def generate_subnet_arn(self, subnet_id: str) -> str:
        """
        Example:
            arn:aws:ec2:us-west-2:123456789012:subnet/subnet-1234567890abcdef0
        """
        return f'arn:aws:ec2:{self.region_name}:{self.account_id}:vpc/{subnet_id}'

    def list_subnets_for_vpc(self, vpc_id: str) -> List[Subnet]:
        # We only search for subnets that match the specified vpc
        response = self.boto3_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        subnets = []
        for subnet in response['Subnets']:
            subnet['Arn'] = self.generate_subnet_arn(subnet['SubnetId'])
            subnet_obj = Subnet.from_api_dict(subnet)
            ec2_instances = list(self.describe_ec2_instances())
            for instance in ec2_instances:
                if instance.subnet_id == subnet['SubnetId']:
                    subnet_obj.ec2_instance = instance
            subnets.append(subnet_obj)
        return subnets

    # TODO: fetch more EC2 instances data
    def describe_ec2_instances(self) -> Iterator[EC2Instance]:
        """
        Collects ec2 instances for client region

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.services.ec2 import AWSCreds, EC2Client
        ... creds = AWSCreds(
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
                instance_arn = self.generate_ec2_arn(instance_data['InstanceId'])
                instance_data['InstanceArn'] = instance_arn
                yield EC2Instance.from_api_dict(instance_data)

    def describe_vpc(self) -> Iterator[VPC]:
        response = self.boto3_client.describe_vpcs()
        for vpc in response['Vpcs']:
            vpc['Arn'] = self.generate_vpc_arn(vpc['VpcId'])
            vpc['Subnets'] = self.list_subnets_for_vpc(vpc['VpcId'])
            yield VPC.from_api_dict(vpc)

    def collect_resources(self):
        return list(self.describe_vpc())
