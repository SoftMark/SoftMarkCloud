from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    age = models.IntegerField(null=True, blank=True)


class AWSCredentials(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    aws_access_key_id = models.CharField(max_length=256)
    aws_secret_access_key = models.CharField(max_length=256)

    class Meta:
        unique_together = ('user', 'aws_access_key_id')
