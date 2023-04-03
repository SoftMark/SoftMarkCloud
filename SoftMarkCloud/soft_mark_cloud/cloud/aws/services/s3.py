import datetime
from dataclasses import dataclass, field
from typing import Iterator, Dict, List

from soft_mark_cloud.cloud.aws.core import AWSGlobalClient, AWSCredentials, AWSResource


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


@dataclass
class S3Bucket(AWSResource):
    """
    S3Bucket Instance dataclass
    """
    name: str
    creation_date: datetime.datetime
    bucket_contents: Dict[str, S3BucketObject] = field(default_factory=dict)

    @property
    def bucket_size(self) -> int:
        return sum(i.size for i in self.bucket_contents.values())

    @classmethod
    def from_api_dict(cls, bucket: dict) -> 'S3Bucket':
        return cls(
            arn=f'arn:aws:s3:::{bucket["Name"]}',
            name=bucket['Name'],
            creation_date=bucket['CreationDate'],
        )

    @property
    def json(self):
        data = self.__dict__
        data['bucket_size'] = self.bucket_size
        data['bucket_contents'] = {arn: bo.__dict__ for arn, bo in self.bucket_contents.items()}
        return data


class S3Client(AWSGlobalClient):
    """
    This class provides S3 API functional
    """

    def __init__(self, credentials: AWSCredentials):
        super().__init__(credentials, service_name='s3')

    def list_s3_buckets_contents(self, bucket_name) -> List[S3BucketObject]:
        contents = self.boto3_client.list_objects(Bucket=bucket_name)
        return [S3BucketObject.from_api_dict(bucket_content) for bucket_content in contents.get('Contents', [])]

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
        resp: dict = self.boto3_client.list_buckets()
        for bucket_dict in resp['Buckets']:
            s3_bucket = S3Bucket.from_api_dict(bucket_dict)
            bucket_contents = self.list_s3_buckets_contents(s3_bucket.name)
            s3_bucket.bucket_contents = {bc.key: bc for bc in bucket_contents}
            yield s3_bucket

    def collect_resources(self) -> List[S3Bucket]:
        return list(self.list_s3_buckets())
