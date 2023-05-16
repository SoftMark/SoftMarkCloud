import datetime

from logging import getLogger
from dataclasses import dataclass, field
from typing import Iterator, List

from soft_mark_cloud.cloud.aws.core import AWSGlobalClient, AWSCreds, AWSResource
from soft_mark_cloud.cloud.aws.services.pricing import PricingClient

from humanize import naturalsize

from soft_mark_cloud.domain import DisplayItem, StringField, ItemsField


logger = getLogger(__name__)


@dataclass
class S3BucketObject:
    """
    S3Bucket content dataclass
    """
    key: str
    size: int
    last_modified: datetime.datetime

    @classmethod
    def from_api_dict(cls, bucket_content: dict) -> 'S3BucketObject':
        return cls(
            key=bucket_content['Key'],
            size=bucket_content['Size'],
            last_modified=bucket_content['LastModified']
        )

    @property
    def domain(self) -> DisplayItem:
        fields = [
            StringField('Size', naturalsize(self.size)),
            StringField('Modified at', self.last_modified.isoformat())
        ]
        return DisplayItem(
            name=self.key,
            item_type='s3_bucket_object',
            fields=fields)

    @property
    def json(self):
        return self.domain.json


@dataclass
class S3Bucket(AWSResource):
    """
    S3Bucket Instance dataclass
    """
    name: str
    creation_date: datetime.datetime
    price_per_hour: float = None
    bucket_contents: List[S3BucketObject] = field(default_factory=list)

    @property
    def price_per_month(self):
        return self.price_per_hour * 24 * 31

    @property
    def bucket_size(self) -> int:
        return sum(bc.size for bc in self.bucket_contents)

    @property
    def bucket_size_gb(self) -> float:
        return self.bucket_size * pow(2, -30)

    @classmethod
    def from_api_dict(cls, bucket: dict) -> 'S3Bucket':
        return cls(
            arn=f'arn:aws:s3:::{bucket["Name"]}',
            name=bucket['Name'],
            creation_date=bucket['CreationDate'],
        )

    @property
    def domain(self) -> DisplayItem:
        fields = [
            StringField('Name', self.name),
            StringField('Created at', self.creation_date.isoformat()),
            StringField('Size', naturalsize(self.bucket_size)),
            StringField('Price per month', f'{round(self.price_per_month, 2)} $'),
            ItemsField('Contents', [bc.domain for bc in self.bucket_contents])
        ]
        return DisplayItem(
            name=self.arn,
            item_type=self.resource_type,
            fields=fields)


class S3Client(AWSGlobalClient):
    """
    This class provides S3 API functional
    """
    service_name = 's3'

    def __init__(self, credentials: AWSCreds):
        super().__init__(credentials)

    def list_s3_buckets_contents(self, bucket_name) -> List[S3BucketObject]:
        contents = self.boto3_client.list_objects(Bucket=bucket_name)
        return [S3BucketObject.from_api_dict(bucket_content) for bucket_content in contents.get('Contents', [])]

    def list_s3_buckets(self) -> Iterator[S3Bucket]:
        """
        Collects s3 bucket instances

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.services.s3 import AWSCreds, S3Client
        ... creds = AWSCreds(
        ...     aws_access_key_id='{aws_access_key_id}',
        ...     aws_secret_access_key='{aws_secret_access_key}'
        ... )
        ... client = S3Client(credentials=creds)
        ... s3_buckets = list(client.list_s3_buckets())
        ... print(s3_buckets)
        out:
           List of S3Bucket class instances.
        """
        self.credentials: AWSCreds
        pricing_client = PricingClient(self.credentials)

        resp: dict = self.boto3_client.list_buckets()
        for bucket_dict in resp['Buckets']:
            s3_bucket = S3Bucket.from_api_dict(bucket_dict)
            s3_bucket.bucket_contents = self.list_s3_buckets_contents(s3_bucket.name)
            s3_bucket.price_per_hour = pricing_client.get_s3_bucket_price(s3_bucket.bucket_size_gb)
            yield s3_bucket

    def collect_resources(self) -> List[S3Bucket]:
        logger.info(f"Receiving s3 buckets")
        return list(self.list_s3_buckets())
