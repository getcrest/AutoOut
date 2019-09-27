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
from psutil import virtual_memory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AutoOut.settings')

# Start dask cluster
no_cpus = multiprocessing.cpu_count()
threads_per_worker = 2
no_workers = math.floor((no_cpus-2)/threads_per_worker)

mem = virtual_memory()

c = LocalCluster(processes=False, n_workers=no_workers, threads_per_worker=threads_per_worker,
                 memory_limit=mem.free/no_workers)
dask_client = Client(c)

application = get_wsgi_application()
