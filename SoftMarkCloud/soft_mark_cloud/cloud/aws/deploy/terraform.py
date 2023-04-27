import os
import subprocess

from pathlib import Path
from dataclasses import dataclass

from soft_mark_cloud.cloud.core import Deployer, DeploySettings
from soft_mark_cloud.cloud.aws.core import AWSCreds
from soft_mark_cloud.cloud.aws.core import AWSRegionalClient


@dataclass
class TerraformSettings(DeploySettings):
    creds: AWSCreds
    region: str

    resource_name: str
    instance_type: str

    repository_url: str = None

    ami: str = 'ami-090f10efc254eaf55'  # Ubuntu ami


class AWSDeployer(Deployer):
    def __init__(self, settings: TerraformSettings):
        super(AWSDeployer, self).__init__(settings)
        self.tf_path = str(Path(__file__).parent / 'tf')
        self.create_df_folder()
        self.__client = AWSRegionalClient(settings.creds, settings.region)

    def create_df_folder(self):
        if not os.path.exists(self.tf_path):
            os.makedirs(self.tf_path)

    def terraform_init(self):
        subprocess.run(["terraform", "init"], cwd=self.tf_path)

    def terraform_apply(self):
        subprocess.run(["terraform", "apply"], cwd=self.tf_path, input="yes\n", encoding="ascii")

    @property
    def tf_file_name(self):
        return "{account_id}_{resource_name}.tf".format(
            account_id=self.__client.account_id,
            resource_name=self.settings.resource_name)

    @property
    def tf_file_path(self):
        return f"{self.tf_path}\\{self.tf_file_name}"

    def remove_tf_file(self):
        os.remove(self.tf_file_path)

    def generate_tf_file(self):
        """
        Generates .tf file
        """
        self.settings: TerraformSettings

        content = """provider "aws" {{
    access_key = "{access_key}"
    secret_key = "{secret_key}"
    region     = "{region}"
}}

resource "aws_instance" "{resource_name}" {{
    ami           = "{ami}"
    instance_type = "{instance_type}"   
}}"""\
            .format(
                access_key=self.settings.creds.aws_access_key_id,
                secret_key=self.settings.creds.aws_secret_access_key,
                region=self.settings.region,
                resource_name=self.settings.resource_name,
                ami=self.settings.ami,
                instance_type=self.settings.instance_type
            )

        with open(self.tf_file_path, "w") as f:
            f.write(content)

    def create_instance(self):
        """
        >>> from soft_mark_cloud.cloud.aws.core import AWSCreds
        >>> from soft_mark_cloud.cloud.aws.deploy.terraform import TerraformSettings, AWSDeployer

        >>> creds = AWSCreds(
        >>>     aws_access_key_id='{aws_access_key_id}',
        >>>     aws_secret_access_key='{aws_secret_access_key}'
        >>> )

        >>> settings = TerraformSettings(
        >>>     creds=creds,
        >>>     region='{region_name}',

        >>>     resource_name='{resource_name}',
        >>>     instance_type='{instance_type}', # 't2.micro' for example
        >>> )

        >>> deployer = AWSDeployer(settings)
        >>> deployer.create_instance()
        """
        self.generate_tf_file()
        self.terraform_init()
        self.terraform_apply()
        self.remove_tf_file()

    def deploy(self):
        self.create_instance()
