from soft_mark_cloud.models import AWSCloudData
from soft_mark_cloud.cloud.cache import CloudCache


class AWSCache(CloudCache):
    CacheModel = AWSCloudData
