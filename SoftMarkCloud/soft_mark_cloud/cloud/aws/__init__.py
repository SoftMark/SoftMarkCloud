import django; django.setup()  # needed for multiprocessing
from .core import *
from .services.pricing import *
from .services.ec2 import *
from .services.s3 import *
