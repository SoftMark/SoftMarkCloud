import datetime
from dataclasses import dataclass, field
from typing import Iterator, List

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
            instance_id=data['InstanceId'],
            instance_type=data['InstanceType'],
            instance_state=data['State']['Name'],
            subnet_id=data['SubnetId'],
            vpc_id=data['VpcId'],
            launch_time=data['LaunchTime'])

    @property
    def json(self):
        data = super().json
        data['launch_time'] = self.launch_time.isoformat()
        return data


@dataclass
class Subnet(AWSResource):
    vpc_id: str
    subnet_id: str
    availability_zone: str
    ec2_instances: List[EC2Instance] = field(default_factory=list)

    @classmethod
    def from_api_dict(cls, subnet: dict) -> 'Subnet':
        return cls(
            arn=subnet['Arn'],
            vpc_id=subnet['VpcId'],
            subnet_id=subnet['SubnetId'],
            availability_zone=subnet['AvailabilityZone'])

    @property
    def json(self):
        data = super().json
        data['ec2_instances'] = [ec2.json for ec2 in self.ec2_instances]
        return data


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
            id=vpc['VpcId'],
            is_default=vpc['IsDefault'],
            state=vpc['State'],
            subnets=vpc['Subnets'])

    @property
    def json(self):
        data = super().json
        data['subnets'] = [s.json for s in self.subnets]
        return data


class EC2Client(AWSRegionalClient):
    """
    This class provides EC2 API functional
    """
    service_name = 'ec2'

    def __init__(self, credentials: AWSCreds, region_name: str):
        super().__init__(credentials, region_name=region_name)

    def generate_arn(self, resource_type: str, resource_id: str) -> str:
        """
        Example: arn:aws:ec2:us-east-1:123456789012:instance/i-012abcd34efghi56
        """
        return f'arn:aws:ec2:{self.region_name}:{self.account_id}:{resource_type}/{resource_id}'

    def list_subnets_for_vpc(self, vpc_id: str) -> List[Subnet]:
        ec2_instances = list(self.describe_ec2_instances())

        # Get subnet data from API. We only search for subnets that match the specified vpc
        subnets = []
        response = self.boto3_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

        # Create subnet objects and attach EC2 instances
        for subnet_data in response['Subnets']:
            subnet_data['Arn'] = self.generate_arn('subnet', subnet_data['SubnetId'])
            subnet_obj = Subnet.from_api_dict(subnet_data)
            subnet_instances = [i for i in ec2_instances if i.subnet_id == subnet_obj.subnet_id]
            subnet_obj.ec2_instances.extend(subnet_instances)
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
                instance_arn = self.generate_arn('instance', instance_data['InstanceId'])
                instance_data['InstanceArn'] = instance_arn
                yield EC2Instance.from_api_dict(instance_data)

    def describe_vpc(self) -> Iterator[VPC]:
        """
        Collects VPCs for client region

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.services.ec2 import AWSCreds, EC2Client
        ... creds = AWSCreds(
        ...     aws_access_key_id='{aws_access_key_id}',
        ...     aws_secret_access_key='{aws_secret_access_key}'
        ... )
        ... client = EC2Client(credentials=creds, region_name='{region_name}')
        ... vpcs = list(client.describe_vpc())
        ... print(vpcs)
        out:
            List of vpc with corresponding subnets.
        """
        response = self.boto3_client.describe_vpcs()
        for vpc in response['Vpcs']:
            vpc['Arn'] = self.generate_arn('vpc', vpc['VpcId'])
            vpc['Subnets'] = self.list_subnets_for_vpc(vpc['VpcId'])
            yield VPC.from_api_dict(vpc)

    def collect_resources(self):
        return list(self.describe_vpc())
