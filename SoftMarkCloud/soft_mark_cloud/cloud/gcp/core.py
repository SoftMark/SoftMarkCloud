from dataclasses import dataclass

from soft_mark_cloud.cloud.core import Credentials, CloudClient


@dataclass
class GCPResource:
    """
    GCP resource dataclass
    """
    arn: str

    @property
    def json(self):
        return self.__dict__


@dataclass
class GCPCreds(Credentials):
    """
    Credentials holder dataclass
    """
    gcp_access_key_id: str
    gcp_secret_access_key: str
