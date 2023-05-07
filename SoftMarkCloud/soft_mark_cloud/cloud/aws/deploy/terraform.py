import time
import multiprocessing
import os
import subprocess
from enum import Enum

from pathlib import Path
from dataclasses import dataclass

from soft_mark_cloud.cloud.aws import EC2Client
from soft_mark_cloud.cloud.aws.status import AWSStatusDao
from soft_mark_cloud.cloud.core import Deployer, DeploySettings
from soft_mark_cloud.cloud.aws.core import AWSCreds
from soft_mark_cloud.models import User


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
    process_name = 'terraform_deploying'

    class Steps(Enum):
        instance_generation = 'Generating instance ...'
        receiving_instance_data = 'Receiving instance data ...'
        instance_initialization = 'Instance initialization ...'

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

output "instance_id" {{
  value = aws_instance.{resource_name}.id
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

        >>>     git_url='{git_url}',
        >>>     manage_path='{manage_path}',
        >>>     requirements_path='{requirements_path}'

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

    def get_instance_id(self) -> str:
        res = subprocess.run(["terraform", "output", 'instance_id'], cwd=self.tf_path, capture_output=True, text=True)
        return res.stdout.strip()[1:-1]

    def deploy(self, user: User):
        self.settings: TerraformSettings
        details = {
            'steps': {
                self.Steps.instance_generation.value: False,
                self.Steps.receiving_instance_data.value: False,
                self.Steps.instance_initialization.value: False
            },
            'url': None
        }
        status = AWSStatusDao.create_status(user=user, process_name=self.process_name, details=details)

        # Creating
        self.create_instance()
        details['steps'][self.Steps.instance_generation.value] = True
        AWSStatusDao.update_status_details(status, details)

        # Receiving data
        public_ip = self.get_instance_public_ip()
        instance_id = self.get_instance_id()
        details['steps'][self.Steps.receiving_instance_data.value] = True
        AWSStatusDao.update_status_details(status, details)

        # Initializing
        ec2_client = EC2Client(self.settings.creds, self.settings.region)
        check_after = 10  # seconds
        while True:
            time.sleep(check_after)

            if not ec2_client.get_ec2_instance(instance_id):
                break

            if ec2_client.check_ec2_instance_initialized(instance_id):
                break

        details['url'] = f"http://{public_ip}:8000"
        details['steps'][self.Steps.instance_initialization.value] = True
        AWSStatusDao.update_status_details(status, details)

        # Completed
        AWSStatusDao.update_status_state(status, done=True)

    def deploy_async(self, user: User):
        multiprocessing.Process(target=self.deploy, args=(user, )).start()
