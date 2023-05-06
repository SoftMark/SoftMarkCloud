import os
import subprocess

from pathlib import Path
from dataclasses import dataclass

from soft_mark_cloud.cloud.core import Deployer, DeploySettings
from soft_mark_cloud.cloud.aws.core import AWSCreds


@dataclass
class TerraformSettings(DeploySettings):
    creds: AWSCreds
    region: str

    resource_name: str
    instance_type: str

    git_url: str
    manage_path: str

    project_path: str = '/var/www/html/yourproject'

    requirements_path: str = ''

    repository_url: str = None

    ami: str = 'ami-090f10efc254eaf55'  # Ubuntu ami


class AWSDeployer(Deployer):
    def __init__(self, settings: TerraformSettings):
        super(AWSDeployer, self).__init__(settings)
        self.settings: TerraformSettings
        self.tf_path = str(Path(__file__).parent / 'tf')
        self.create_df_folder()
        self.account_id = self.settings.creds.get_account_id()

    def create_df_folder(self):
        if not os.path.exists(self.tf_path):
            os.makedirs(self.tf_path)

    def terraform_init(self):
        subprocess.run(["terraform", "init"], cwd=self.tf_path)

    def terraform_apply(self):
        subprocess.run(["terraform", "apply"], cwd=self.tf_path, input="yes\n", encoding="ascii")

    @property
    def tf_file_name(self):
        self.settings: TerraformSettings
        return "{account_id}_{resource_name}.tf".format(
            account_id=self.account_id,
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
    key_name      = "terraform-key"
    subnet_id     = "subnet-0b857da7631a9302e"
    security_groups = ["sg-0b02b860a5a012468"]
    
    user_data     = <<-EOF
            #!/bin/bash
            sudo mkdir -p {project_path}
            git clone {git_url} {project_path}
            
            sudo apt-get update
            
            sudo DEBIAN_FRONTEND=noninteractive apt-get -y install python3-venv
            sudo apt-get -y install python3-django
            python3 -m venv env
            source /env/bin/activate
            export ALLOWED_HOST=$(curl ifconfig.me)
            pip3 install django
            pip3 install -r {project_path}{requirements_path}
            cd {project_path}{manage_path}
            sudo /env/bin/python manage.py migrate
            python manage.py runserver 0.0.0.0:8000
            EOF
}}

output "public_ip" {{
  value = aws_instance.{resource_name}.public_ip
}}"""\
            .format(
                access_key=self.settings.creds.aws_access_key_id,
                secret_key=self.settings.creds.aws_secret_access_key,
                region=self.settings.region,
                resource_name=self.settings.resource_name,
                ami=self.settings.ami,
                instance_type=self.settings.instance_type,
                git_url=self.settings.git_url,
                project_path=self.settings.project_path,
                manage_path=self.settings.manage_path,
                requirements_path=self.settings.requirements_path
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

    def get_instance_public_ip(self) -> str:
        res = subprocess.run(["terraform", "output", 'public_ip'], cwd=self.tf_path, capture_output=True, text=True)
        return res.stdout.strip()[1:-1]

    def deploy(self) -> str:
        self.create_instance()
        ip = self.get_instance_public_ip()
        return f"http://{ip}:8000"
