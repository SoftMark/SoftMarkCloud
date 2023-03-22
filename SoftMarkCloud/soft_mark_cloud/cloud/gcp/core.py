from soft_mark_cloud.cloud.core import Credentials


class GCPCredentials(Credentials):
    aws_access_key_id: str
    aws_secret_access_key: str
