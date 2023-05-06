import django; django.setup()  # needed for multiprocessing
from .services.ec2 import *
from .services.s3 import *
