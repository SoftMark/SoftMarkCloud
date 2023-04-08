from dataclasses import dataclass


@dataclass
class Credentials:
    """
    Abstract credential class
    """
    pass


class CloudClient:
    """
    Abstract cloud client class
    """
    def __init__(self, credentials: Credentials):
        self.credentials = credentials


class CloudCollector:
    """
    Abstract cloud collector class
    """
    def collect_all(self):
        pass
