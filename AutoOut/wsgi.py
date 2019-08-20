"""
WSGI config for AutoOut project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import math
import multiprocessing
import os

from distributed import LocalCluster, Client
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AutoOut.settings')

# Start dask cluster
no_cpus = multiprocessing.cpu_count()
threads_per_worker = 2
no_workers = math.floor((no_cpus-1)/threads_per_worker)

c = LocalCluster(processes=False, n_workers=no_workers, threads_per_worker=threads_per_worker)
dask_client = Client(c)

application = get_wsgi_application()
