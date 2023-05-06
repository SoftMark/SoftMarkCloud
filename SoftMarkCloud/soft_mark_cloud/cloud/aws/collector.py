import multiprocessing

from soft_mark_cloud.models import User
from soft_mark_cloud.cloud.aws.cache import AWSCache
from soft_mark_cloud.cloud.aws.status import AWSStatusDao
from soft_mark_cloud.cloud.core import CloudCollector
from soft_mark_cloud.cloud.aws.core import AWSCreds, AWSRegionalClient, AWSGlobalClient


class AWSCollector(CloudCollector):
    """
    Examples
    --------

    >>> from pprint import pprint
    >>> from soft_mark_cloud.cloud.aws.collector import AWSCollector
    >>> from soft_mark_cloud.cloud.aws.services.ec2 import AWSCreds
    ... creds = AWSCreds(
    ...     aws_access_key_id='{aws_access_key_id}',
    ...     aws_secret_access_key='{aws_secret_access_key}'
    ... )
    >>> pprint(AWSCollector(creds).collect_all())
    out:
        All collected data from AWS
    """
    process_name = 'AWS_data_collecting'

    all_regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-south-1', 'ap-northeast-2', 'ap-northeast-3',
                   'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2',
                   'eu-west-3', 'eu-north-1', 'sa-east-1']

    def __init__(self, credentials: AWSCreds):
        self.credentials = credentials

    def collect_all(self) -> dict:
        res = {
            'regional': {
                r: {} for r in self.all_regions
            },
            'global': {}
        }

        for region in self.all_regions:
            for regional_client_cls in AWSRegionalClient.__subclasses__():
                regional_client = regional_client_cls(self.credentials, region)
                res['regional'][region].update(regional_client.collect_all())

        for global_client_cls in AWSGlobalClient.__subclasses__():
            global_client = global_client_cls(self.credentials)
            res['global'].update(global_client.collect_all())

        return res

    def run(self, user: User):
        status = AWSStatusDao.create_status(user=user, process_name=self.process_name)
        aws_data = self.collect_all()
        AWSStatusDao.update_status_state(status, done=True)
        AWSCache.save_cache(user, aws_data)

    def run_async(self, user: User):
        multiprocessing.Process(target=self.run, args=(user, )).start()
