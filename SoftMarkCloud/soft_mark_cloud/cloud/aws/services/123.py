from soft_mark_cloud.cloud.aws.services.s3 import AWSCredentials, S3Client
from pprint import pprint
creds = AWSCredentials(
    aws_access_key_id='AKIAQE53DWDHJAFLK6OU',
    aws_secret_access_key='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'
)
client = S3Client(credentials=creds)
s3_buckets = list(client.list_s3_buckets())
pprint(s3_buckets)
