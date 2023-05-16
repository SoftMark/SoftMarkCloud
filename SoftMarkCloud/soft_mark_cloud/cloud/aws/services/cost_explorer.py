import json
from datetime import datetime
from dataclasses import dataclass
from typing import List

from soft_mark_cloud.cloud.aws import AWSGlobalClient


@dataclass
class CostData:
    month: str
    ec2: float
    ebs: float
    s3: float

    @property
    def total(self):
        return self.ec2 + self.ebs + self.s3


def gen_cost_and_usage(month: str):
    month_map = {'Jan': [45, 20, 15], 'Feb': [51, 10, 12], 'Mar': [39, 7, 10], 'Apr': [75, 15, 0], 'May': [36, 10, 5]}

    # with open('../mock/cost_and_usage.json', 'r', encoding='utf-8') as mock_file:
    #     mock_data = json.loads(mock_file.read())
    return CostData(month, *month_map.get(month, [0, 0, 0]))


class CostExplorerClient(AWSGlobalClient):
    """
    This class provides S3 API functional
    """
    service_name = 'ce'

    def get_cost_and_usage(self, start_date: datetime, end_date: datetime):
        query = {
            "TimePeriod": {
                "Start": start_date,
                "End": end_date
            },
            "Granularity": "MONTHLY",
            "Metrics": [
                "UnblendedCost"
            ]
        }
        return self.boto3_client.get_cost_and_usage(**query)

    def get_billing_data(self) -> List[CostData]:
        # return  self.get_cost_and_usage()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
        return [gen_cost_and_usage(month) for month in months]
