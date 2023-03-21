from dataclasses import dataclass
from MyPersonalData.S3Buckets_SecreKeys import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

import boto3
import datetime


@dataclass
class S3BucketObject:
    key: str
    size: int
    last_modified: datetime.datetime


@dataclass
class S3Bucket:
    name: str
    creation_date: datetime.datetime
    bucket_objects: list


s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

bucket_list = []
resp = s3.list_buckets()

for bucket in resp['Buckets']:
    bucket_name = bucket['Name']
    bucket_creation_date = bucket['CreationDate']
    bucket_objects_list = []
    response = s3.list_objects(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            bucket_object = S3BucketObject(obj['Key'], obj['Size'], obj['LastModified'])
            bucket_objects_list.append(bucket_object)
    bucket_list.append(S3Bucket(bucket_name, bucket_creation_date, bucket_objects_list))

for bucket in bucket_list:
    print(bucket.name)
