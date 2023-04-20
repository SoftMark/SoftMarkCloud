import json
from typing import Optional, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model

from soft_mark_cloud.models import User


class CloudCache:
    CacheModel = Model

    @classmethod
    def get_cache(cls, user: User) -> Optional[CacheModel]:
        """
        Gets cache for specified user
        """
        try:
            return cls.CacheModel.objects.get(user=user)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def save_cache(cls, user: User, data: Union[str, dict]) -> CacheModel:
        """
        Saves cache for specified user
        """
        if isinstance(data, dict):
            data = json.dumps(data)

        if cache := cls.get_cache(user):
            cache.data_json = data
        else:
            cache = cls.CacheModel(
                user=user,
                data_json=data
            )

        return cache.save()

    @classmethod
    def clear_cache(cls, user: User):
        """
        Clears cache for specified user
        """
        if cache := cls.get_cache(user):
            cache.delete()

    @classmethod
    def get_cache_data_json(cls, user: User) -> Optional[str]:
        """
        Gets aws cache data json for specified user
        """
        if cache := cls.get_cache(user):
            return cache.data_json
        else:
            return 'No data'
