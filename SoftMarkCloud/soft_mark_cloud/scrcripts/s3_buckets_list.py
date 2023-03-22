from dataclasses import dataclass
from MyPersonalData.S3Buckets_SecreKeys import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

import boto3
import datetime


@dataclass
class S3BucketContent:
    key: str
    size: int
    last_modified: datetime.datetime


@dataclass
class S3Bucket:
    name: str
    creation_date: datetime.datetime
    bucket_contents: dict

    @property
    def bucket_size(self) -> int:
        total_size = 0
        for content in self.bucket_contents.values():
            total_size += content.size
        return total_size


def list_s3_buckets_contents(bucket_name: str, s3) -> dict:
    bucket_contents_dict = {}
    response = s3.list_objects(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            bucket_contents_dict[obj['Key']] = S3BucketContent(obj['Key'], obj['Size'], obj['LastModified'])
    return bucket_contents_dict


def list_s3_buckets(key_id: str, access_key: str) -> list:
    s3 = boto3.client(
        's3',
        aws_access_key_id=key_id,
        aws_secret_access_key=access_key,
    )
    bucket_list = []
    resp = s3.list_buckets()
    for bucket in resp['Buckets']:
        bucket_name = bucket['Name']
        bucket_creation_date = bucket['CreationDate']
        bucket_list.append(S3Bucket(bucket_name, bucket_creation_date, list_s3_buckets_contents(bucket_name, s3)))
    return bucket_list


if __name__ == '__main__':
    print(list_s3_buckets(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY))
