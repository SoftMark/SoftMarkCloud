from dataclasses import dataclass
from typing import Dict, Union
from MyPersonalData.S3Buckets_SecreKeys import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

import boto3
import datetime


@dataclass
class S3Bucket:
    name: str
    creation_date: datetime.datetime
    bucket_objects: Dict[str, Dict[str, Union[int, datetime.datetime]]]


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
    object_dict = {}
    response = s3.list_objects(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            object_dict[obj['Key']] = {
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            }
    bucket_list.append(S3Bucket(bucket_name, bucket_creation_date, object_dict))

for bucket in bucket_list:
    print(bucket.name)
