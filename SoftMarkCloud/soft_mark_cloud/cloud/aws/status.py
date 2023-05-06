from typing import Optional

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
    def delete_status(cls, user: User, process_name: str):
        try:
            status = AWSProcessStatus.objects.get(user=user, process_name=process_name)
            status.delete()
        except ObjectDoesNotExist:
            return None

    @classmethod
    def update_status_state(cls, status: AWSProcessStatus, done: bool):
        status.done = done
        status.save()

    @classmethod
    def update_status_details(cls, status: AWSProcessStatus, details: str):
        status.details_json = details
        status.save()

    @classmethod
    def create_status(cls, user: User, process_name: str, details: str = None) -> AWSProcessStatus:
        if cls.get_status(user, process_name):
            cls.delete_status(user, process_name)

        status = AWSProcessStatus(
            user=user,
            process_name=process_name,
            details_json=details
        )
        status.save()
        return status
