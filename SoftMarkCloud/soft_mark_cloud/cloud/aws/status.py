import json
from typing import Optional, Union
from datetime import datetime, timedelta, timezone

from django.core.exceptions import ObjectDoesNotExist

from soft_mark_cloud.models import AWSProcessStatus, User


class AWSStatusDao:
    @classmethod
    def get_status(cls, user: User, process_name: str) -> Optional[AWSProcessStatus]:
        try:
            return AWSProcessStatus.objects.get(user=user, process_name=process_name)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def is_expired(cls, status: AWSProcessStatus, expiration_time: int):
        if not status.done and not status.failed:
            if status.created_at + timedelta(seconds=expiration_time) < datetime.now(tz=timezone.utc):
                return True
        return False

    @classmethod
    def check_expired(cls, status: AWSProcessStatus, expiration_time: int):
        if cls.is_expired(status, expiration_time):
            status.failed = True
            status.save()
        return status

    @classmethod
    def delete_status(cls, user: User, process_name: str):
        try:
            status = AWSProcessStatus.objects.get(user=user, process_name=process_name)
            status.delete()
        except ObjectDoesNotExist:
            return None

    @classmethod
    def delete_all_statuses(cls, user: User):
        try:
            status = AWSProcessStatus.objects.filter(user=user)
            status.delete()
        except ObjectDoesNotExist:
            return None

    @classmethod
    def update_status_state(cls, status: AWSProcessStatus, done: bool):
        status.done = done
        status.save()

    @classmethod
    def update_status_details(cls, status: AWSProcessStatus, details: Union[str, dict]):
        if details and isinstance(details, dict):
            details = json.dumps(details, indent=4)

        status.details_json = details
        status.save()
        return status

    @classmethod
    def create_status(cls, user: User, process_name: str, details: Union[str, dict] = None) -> AWSProcessStatus:
        if details and isinstance(details, dict):
            details = json.dumps(details, indent=4)

        if cls.get_status(user, process_name):
            cls.delete_status(user, process_name)

        status = AWSProcessStatus(
            user=user,
            process_name=process_name,
            details_json=details
        )
        status.save()
        return status
