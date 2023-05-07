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


@dataclass
class DeploySettings:
    """
    Abstract deploy settings class
    """


class Deployer:
    """
    Abstract deployer class
    """
    def __init__(self, settings: DeploySettings):
        self.settings = settings

    def deploy(self):
        pass
