from dataclasses import dataclass
from soft_mark_cloud.cloud.aws.core import AWSRegionalClient, AWSCreds, AWSResource
from typing import Iterator, Dict


@dataclass
class Subnet(AWSResource):
    vpc_id: str
    subnet_id: str
    availability_zone: str

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
    subnets: Dict[str, Subnet]

    @classmethod
    def from_api_dict(cls, vpc: dict) -> 'VPC':
        return cls(
            arn=vpc['Arn'],
            resource_type='vpc',
            id=vpc['VpcId'],
            is_default=vpc['IsDefault'],
            state=vpc['State'],
            subnets=vpc['Subnets'])


class VPCClient(AWSRegionalClient):
    """
    This class provides VPC API functional
    """
    service_name = 'ec2'

    def __init__(self, credentials: AWSCreds, region_name: str):
        super().__init__(credentials, region_name=region_name)

    def generate_vpc_arn(self, vpc_id: str) -> str:
        """
        Example:
            arn:aws:ec2:<region>:<account_id>:vpc/<vpc_id>
            arn:aws:ec2:us-east-1:123456789012:vpc/vpc-1234567890abcdef0
        """
        return f'arn:aws:ec2:{self.region_name}:{self.account_id}:vpc/{vpc_id}'

    def generate_subnet_arn(self, subnet_id: str) -> str:
        """
        Example:
            arn:aws:ec2:<region>:<account-id>:subnet/<subnet-id>
            arn:aws:ec2:us-west-2:123456789012:subnet/subnet-1234567890abcdef0
        """
        return f'arn:aws:ec2:{self.region_name}:{self.account_id}:vpc/{subnet_id}'

    def list_subnets_for_vpc(self, vpc_id: str) -> Dict[str, Subnet]:
        # We only search for subnets that match the specified vpc
        response = self.boto3_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        subnets_dict = {}
        for subnet in response['Subnets']:
            subnet['Arn'] = self.generate_subnet_arn(subnet['SubnetId'])
            subnet_obj = Subnet.from_api_dict(subnet)
            subnets_dict[subnet_obj.arn] = subnet_obj
        return subnets_dict

    def describe_vpc(self) -> Iterator[VPC]:
        """
        Collects vpc instances for client region

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.services.ec2 import AWSCreds, EC2Client
        ... creds = AWSCreds(
        ...     aws_access_key_id='{aws_access_key_id}',
        ...     aws_secret_access_key='{aws_secret_access_key}'
        ... )
        ... client = VPCClient(credentials=creds, region_name='{region_name}')
        ... vpcs = list(client.describe_vpc())
        ... print(vpcs)
        out:
            List of vpc with corresponding subnets.
        """
        response = self.boto3_client.describe_vpcs()
        for vpc in response['Vpcs']:
            vpc['Arn'] = self.generate_vpc_arn(vpc['VpcId'])
            vpc['Subnets'] = self.list_subnets_for_vpc(vpc['VpcId'])
            yield VPC.from_api_dict(vpc)
