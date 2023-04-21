from dataclasses import dataclass
from google.cloud import compute_v1

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
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
