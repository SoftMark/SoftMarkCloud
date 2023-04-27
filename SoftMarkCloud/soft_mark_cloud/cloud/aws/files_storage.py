from typing import List

from soft_mark_cloud.cloud.files_storage import CloudStorage
from soft_mark_cloud.cloud.aws.core import AWSCreds
from soft_mark_cloud.cloud.aws.services.s3 import S3Client


class AWSStorage(CloudStorage):
    def __init__(self, credentials: AWSCreds):
        super().__init__(credentials)
        self.name_bucket = None

    def get_bucket_names(self) -> List[str]:
        """
        Get s3 bucket names

        Examples
        --------
        >>> from soft_mark_cloud.cloud.aws.files_storage import AWSStorage, AWSCreds
        ... creds = AWSCreds(
        ...     aws_access_key_id='{aws_access_key_id}',
        ...     aws_secret_access_key='{aws_secret_access_key}'
        ... )
        ... storage = AWSStorage(credentials=creds)
        ... bucket_names = list(storage.get_bucket_names())
        ... print(bucket_names)
        out:
           List of S3Bucket class instances.
        """
        return [i.name for i in S3Client(self.credentials).list_s3_buckets()]

    def select_bucket_name(self, _name_bucket):
        self.name_bucket = _name_bucket

    def get_files_keys(self) -> List[str]:
        return [i.key for i in S3Client(self.credentials).list_s3_buckets_contents(self.name_bucket)]

    def get_file(self, _key: str) -> bytes:
        return S3Client(self.credentials).get_object_contents(self.name_bucket, _key)

    def put_file(self, _key: str, body_file: bytes) -> None:
        pass

    def delete_file(self, _key: str) -> None:
        pass
