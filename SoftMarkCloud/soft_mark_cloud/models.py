import json

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    age = models.IntegerField(null=True, blank=True)
    email = models.EmailField(unique=True)


class AWSCredentials(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    aws_access_key_id = models.CharField(max_length=256)
    aws_secret_access_key = models.CharField(max_length=256)

    class Meta:
        unique_together = ('user', 'aws_access_key_id')


class AWSCloudData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    data_json = models.TextField()

    @property
    def data(self):
        return json.loads(self.data_json)


class AWSProcessStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    process_name = models.CharField(max_length=256)

    done = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)

    details_json = models.TextField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def details(self):
        if self.details_json:
            return json.loads(self.details_json)
        return None

    class Meta:
        unique_together = ('user', 'process_name')
