import multiprocessing

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime

from soft_mark_cloud.cloud.aws import AWSCreds
from soft_mark_cloud.cloud.aws.services.ec2 import EC2Client
from soft_mark_cloud.cloud.aws.services.s3 import S3Client
from soft_mark_cloud.cloud.aws.services.cost_explorer import CostExplorerClient
from soft_mark_cloud.cloud.aws.status import AWSStatusDao
from soft_mark_cloud.models import User


class AWSBilling:
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    process_name = 'aws_billing'

    def __init__(self, creds: AWSCreds):
        self.creds = creds

    def get_ec2_price_per_month(self):
        price = 0
        for region in ['eu-central-1']:
            ec2_client = EC2Client(self.creds, region)
            for instance in ec2_client.describe_ec2_instances():
                if instance.instance_state == 'running':
                    price += instance.price_per_month
        return price

    def get_s3_price_per_month(self):
        price = 0
        s3_client = S3Client(self.creds)
        for bucket in s3_client.list_s3_buckets():
            price += bucket.price_per_month
        return price

    @property
    def empty_billing_data(self):
        fig = make_subplots(rows=1, cols=1)
        fig.update_layout(
            title='AWS Monthly Billing',
            xaxis_title='Month',
            yaxis_title='Billing Amount ($)',
            barmode='relative'
        )
        return {
            'graph_html': fig.to_html(),
            'annual': 0,
        }

    def build_billing_data(self):
        fig = make_subplots(rows=1, cols=1)

        billing_data = CostExplorerClient(self.creds).get_billing_data()
        zeros = [0, 0]

        # Billing
        ec2 = [bd.ec2 for bd in billing_data]
        fig.add_trace(
            go.Bar(x=self.months, y=ec2 + zeros, name='EC2 (Amazon Elastic Compute Cloud)', opacity=0.8, marker_color='#F64C72'),
            row=1, col=1
        )
        ec2_price_per_month = self.get_ec2_price_per_month()
        ec2_curent_month_prediction = ec2_price_per_month * datetime.now().day / 31
        fig.add_trace(
            go.Bar(x=self.months, y=[0] * (len(billing_data) - 1) + [ec2_curent_month_prediction, ec2_price_per_month],
                   opacity=0.3, marker_color='#F64C72', name='EC2 Prediction'),

            row=1, col=1
        )

        ebs = [bd.ebs for bd in billing_data]
        fig.add_trace(
            go.Bar(x=self.months, y=ebs + zeros, name='EBS (Amazon Elastic Block Store)', opacity=0.7, marker_color='#4056A1'),
            row=1, col=1
        )

        s3 = [bd.s3 for bd in billing_data]
        fig.add_trace(
            go.Bar(x=self.months, y=s3 + zeros, name='S3 (Amazon Simple Storage Service)', opacity=0.8, marker_color='#41B3A3'),
            row=1, col=1
        )
        s3_price_per_month = self.get_s3_price_per_month() * 1000
        s3_curent_month_prediction = s3_price_per_month * datetime.now().day / 31
        fig.add_trace(
            go.Bar(x=self.months, y=[0] * (len(billing_data) - 1) + [s3_curent_month_prediction, s3_price_per_month],
                   opacity=0.3, marker_color='#41B3A3', name='S3 Prediction'),

            row=1, col=1
        )

        fig.update_layout(
            title='AWS Monthly Billing',
            xaxis_title='Month',
            yaxis_title='Billing Amount ($)',
            barmode='relative'
        )
        return {
            'graph_html': fig.to_html(),
            'annual': round(sum(d.total for d in billing_data), 2),
            'month': round(billing_data[-1].total, 2),
            'this_month_prediction': round(billing_data[-1].total, 2) + round(
                ec2_curent_month_prediction + s3_curent_month_prediction, 2),
            'next_month_prediction': round(ec2_price_per_month + s3_price_per_month, 2)
        }

    def run(self, user: User):
        previous_status = AWSStatusDao.get_status(user, self.process_name)
        details = previous_status.details if previous_status else self.empty_billing_data

        status = AWSStatusDao.create_status(user=user, process_name=self.process_name, details=details)

        billing_data = self.build_billing_data()

        AWSStatusDao.update_status_details(status, details=billing_data)
        AWSStatusDao.update_status_state(status, done=True)

    def run_async(self, user: User):
        multiprocessing.Process(target=self.run, args=(user,)).start()
