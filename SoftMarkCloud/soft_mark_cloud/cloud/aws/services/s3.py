import datetime
from dataclasses import dataclass, field
from typing import Iterator, List

from soft_mark_cloud.cloud.aws.core import AWSGlobalClient, AWSCreds, AWSResource

from humanize import naturalsize

from soft_mark_cloud.domain import DisplayItem, StringField, ItemsField


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
            StringField('key', self.key),
            StringField('size', naturalsize(self.size)),
            StringField('last_modified', self.last_modified.isoformat())
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
    bucket_contents: List[S3BucketObject] = field(default_factory=list)

    @property
    def bucket_size(self) -> int:
        return sum(bc.size for bc in self.bucket_contents)

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
            StringField('name', self.name),
            StringField('creation_date', self.creation_date.isoformat()),
            StringField('bucket_size', naturalsize(self.bucket_size)),
            ItemsField('bucket_contents', [bc.domain for bc in self.bucket_contents])
        ]
        return DisplayItem(
            name=self.name,
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
        resp: dict = self.boto3_client.list_buckets()
        for bucket_dict in resp['Buckets']:
            s3_bucket = S3Bucket.from_api_dict(bucket_dict)
            s3_bucket.bucket_contents = self.list_s3_buckets_contents(s3_bucket.name)
            yield s3_bucket

    def collect_resources(self) -> List[S3Bucket]:
        return list(self.list_s3_buckets())
