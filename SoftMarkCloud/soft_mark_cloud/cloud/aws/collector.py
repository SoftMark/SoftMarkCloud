from soft_mark_cloud.cloud.core import CloudCollector
from soft_mark_cloud.cloud.aws.core import AWSCredentials, AWSRegionalClient, AWSGlobalClient


class AWSCollector(CloudCollector):
    all_regions = 'eu-central-1',  # TODO: add more regions

    def __init__(self, credentials: AWSCredentials):
        self.credentials = credentials

    def collect_all(self) -> dict:
        res = {
            'regional': {
                r: {} for r in self.all_regions
            },
            'global': {}
        }

        for region in self.all_regions:
            for client_cls in AWSRegionalClient.__subclasses__():
                regional_client = client_cls(self.credentials, region)
                res['regional'][region].update(regional_client.collect_all())

        for client_cls in AWSGlobalClient.__subclasses__():
            global_client = client_cls(self.credentials)
            res['global'].update(global_client.collect_all())

        return res
