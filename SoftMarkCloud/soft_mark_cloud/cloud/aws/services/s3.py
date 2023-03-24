import datetime
from dataclasses import dataclass
from typing import Iterator, Dict

from soft_mark_cloud.cloud.aws.core import AWSGlobalClient, AWSCredentials


@dataclass
class S3BucketObject:
    """
    S3Bucket content dataclass
    """
    key: str
    size: int
    last_modified: datetime.datetime

    @classmethod
    def from_bucket_contents(cls, bucket_contents: Dict[str, dict]) -> Dict[str, 'S3BucketObject']:
        if not bucket_contents:
            return {}
        return {obj['Key']: cls(
            key=obj['Key'],
            size=obj['Size'],
            last_modified=obj['LastModified']
        ) for obj in bucket_contents.values()}


@dataclass
class S3Bucket:
    """
    S3Bucket Instance dataclass
    """
    name: str
    creation_date: datetime.datetime
    bucket_contents: Dict[str, 'S3BucketObject']

    @property
    def bucket_size(self) -> int:
        return sum(i.size for i in self.bucket_contents.values())

    @classmethod
    def from_api_dict(cls, bucket: dict, client) -> 'S3Bucket':
        contents = client.list_objects(Bucket=bucket['Name'])['Contents']
        if not contents:
            bucket_contents = {}
        else:
            bucket_contents = S3BucketObject.from_bucket_contents({obj['Key']: obj for obj in contents})
        return cls(
            name=bucket['Name'],
            creation_date=bucket['CreationDate'],
            bucket_contents=bucket_contents
        )


class S3Client(AWSGlobalClient):
    """
    This class provides S3 API functional
    """
    def __init__(self, credentials: AWSCredentials):
        super().__init__(credentials, service_name='s3')

    def list_s3_buckets_contents(self) -> dict:
        bucket_contents_dict = {}
        response = self.client.list_objects()
        if 'Contents' in response:
            for obj in response['Contents']:
                bucket_contents_dict[obj['Key']] = S3BucketObject(obj['Key'], obj['Size'], obj['LastModified'])
        return bucket_contents_dict

    def describe_s3bucket_instances(self) -> Iterator[S3Bucket]:
        """
        Collects s3 bucket instances

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.services.s3 import AWSCredentials, S3Client
        ... creds = AWSCredentials(
        ...     aws_access_key_id='{aws_access_key_id}',
        ...     aws_secret_access_key='{aws_secret_access_key}'
        ... )
        ... client = S3Client(credentials=creds)
        ... s3_buckets = list(client.describe_s3bucket_instances())
        ... print(s3_buckets)
        out:
           List of S3Bucket class instances.
        """
        resp: dict = self.client.list_buckets()
        for bucket in resp['Buckets']:
            yield S3Bucket.from_api_dict(bucket, self.client)
