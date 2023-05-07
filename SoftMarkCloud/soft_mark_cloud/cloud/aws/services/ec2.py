import datetime
from dataclasses import dataclass, field
from typing import Iterator, List, Iterable, Optional

from soft_mark_cloud.cloud.aws.core import AWSRegionalClient, AWSCreds, AWSResource
from soft_mark_cloud.domain import DisplayItem, StringField, ItemsField


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
            subnet_id=data.get('SubnetId'),
            vpc_id=data.get('VpcId'),
            launch_time=data['LaunchTime'])

    @property
    def domain(self) -> DisplayItem:
        fields = [
            StringField('instance_id', self.instance_id),
            StringField('instance_type', self.instance_type),
            StringField('instance_state', self.instance_state),
            StringField('subnet_id', self.subnet_id),
            StringField('vpc_id', self.vpc_id),
            StringField('launch_time', self.launch_time.isoformat())
        ]
        return DisplayItem(
            name=self.instance_id,
            item_type=self.__class__.__name__.lower(),
            fields=fields)


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
    def domain(self) -> DisplayItem:
        fields = [
            StringField('subnet_id', self.subnet_id),
            StringField('vpc_id', self.vpc_id),
            StringField('availability_zone', self.availability_zone),
            ItemsField('ec2_instances', [ec2.domain for ec2 in self.ec2_instances])
        ]
        return DisplayItem(
            name=self.subnet_id,
            item_type=self.__class__.__name__.lower(),
            fields=fields)


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
    def domain(self) -> DisplayItem:
        fields = [
            StringField('id', self.id),
            StringField('is_default', str(self.is_default)),
            StringField('state', self.state),
            ItemsField('subnets', [s.domain for s in self.subnets])
        ]
        return DisplayItem(
            name=self.id,
            item_type=self.resource_type,
            fields=fields)


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
            subnet_obj.ec2_instances = subnet_instances
            subnets.append(subnet_obj)

        return subnets

    def check_ec2_instance_initialized(self, instance_id: str) -> bool:
        resp = self.boto3_client.describe_instance_status(InstanceIds=[instance_id])
        status = resp['InstanceStatuses'][0]
        inst_state = status['InstanceState']['Name'] == 'running'
        inst_status = status['InstanceStatus']['Status'] == 'ok'
        sys_status = status['SystemStatus']['Status'] == 'ok'
        return inst_state and inst_status and sys_status

    def get_ec2_instance(self, instance_id: str) -> Optional[EC2Instance]:
        if instances := [*self.describe_ec2_instances(instance_id)]:
            return instances[0]

    # TODO: fetch more EC2 instances data
    def describe_ec2_instances(self, *instance_ids: str) -> Iterator[EC2Instance]:
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
        kwargs = {}
        if instance_ids:
            kwargs.update({'InstanceIds': [*instance_ids]})

        resp: dict = self.boto3_client.describe_instances(**kwargs)
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
