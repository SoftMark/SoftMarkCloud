import json
from typing import Optional

from soft_mark_cloud.cloud.aws import AWSRegionalClient, AWSCreds


class PricingClient(AWSRegionalClient):
    """
    This class provides Pricing API functional
    """
    service_name = 'pricing'

    def __init__(self, credentials: AWSCreds, region_name: str = None):
        super().__init__(credentials, region_name='us-east-1')

    def get_resource_price(self, service_code, filters) -> Optional[float]:
        """
        Gets price per hour for resource
        """
        resp = self.boto3_client.get_products(
            ServiceCode=service_code,
            Filters=filters,
            FormatVersion='aws_v1')

        price_list = json.loads(resp['PriceList'][0])
        price_dimensions = [*price_list['terms']['OnDemand'].values()][0]['priceDimensions']

        for key in price_dimensions.keys():
            price = price_dimensions[key]['pricePerUnit']['USD']
            return float(price)

    def get_ec2_instance_price(self, instance_type: str) -> float:
        """
        Gets price per hour for ec2 instance
        """
        filters = [
            {
                'Type': 'TERM_MATCH',
                'Field': 'instanceType',
                'Value': instance_type
            },
            {
                'Type': 'TERM_MATCH',
                'Field': 'operatingSystem',
                'Value': 'Linux'
            },
            {
                'Type': 'TERM_MATCH',
                'Field': 'capacitystatus',
                'Value': 'Used'
            }
        ]
        return self.get_resource_price(
            service_code='AmazonEC2',
            filters=filters)

    def get_s3_bucket_price(self, bucket_size_gb: float) -> float:
        """
        Gets price per hour for s3 bucket
        """
        filters = [
            {
                'Type': 'TERM_MATCH',
                'Field': 'productFamily',
                'Value': 'Storage'
            }
        ]
        price_per_gb = self.get_resource_price(
            service_code='AmazonS3',
            filters=filters)

        return price_per_gb * bucket_size_gb
