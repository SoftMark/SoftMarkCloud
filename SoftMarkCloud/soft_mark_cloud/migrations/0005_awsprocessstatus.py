# Generated by Django 4.2 on 2023-05-06 19:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('soft_mark_cloud', '0004_awsclouddata'),
    ]

    operations = [
        migrations.CreateModel(
            name='AWSProcessStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('process_name', models.CharField(max_length=256)),
                ('done', models.BooleanField(default=False)),
                ('details_json', models.TextField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'process_name')},
            },
        ),
    ]