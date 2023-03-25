import datetime
from dataclasses import dataclass
from typing import Iterator, Dict, List

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
    def from_api_dict(cls, bucket: dict) -> 'S3Bucket':
        return cls(
            name=bucket['Name'],
            creation_date=bucket['CreationDate'],
            bucket_contents={}
        )


class S3Client(AWSGlobalClient):
    """
    This class provides S3 API functional
    """

    def __init__(self, credentials: AWSCredentials):
        super().__init__(credentials, service_name='s3')

    def list_s3_buckets_contents(self, bucket_name) -> List[S3BucketObject]:
        contents = self.client.list_objects(Bucket=bucket_name)
        return [S3BucketObject(
            key=obj['Key'],
            size=obj['Size'],
            last_modified=obj['LastModified']
        ) for obj in contents.get('Contents', [])]

    def list_s3_buckets(self) -> Iterator[S3Bucket]:
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
        ... s3_buckets = list(client.list_s3_buckets())
        ... print(s3_buckets)
        out:
           List of S3Bucket class instances.
        """
        resp: dict = self.client.list_buckets()
        for bucket in resp['Buckets']:
            bucket_contents = {
                obj.key: obj
                for obj in self.list_s3_buckets_contents(bucket['Name'])}
            s3_bucket = S3Bucket.from_api_dict(bucket)
            s3_bucket.bucket_contents = bucket_contents
            yield s3_bucket
