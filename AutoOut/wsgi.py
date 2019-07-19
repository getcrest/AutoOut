"""
WSGI config for AutoOut project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from distributed import LocalCluster, Client
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AutoOut.settings')

# Start dask cluster
c = LocalCluster(processes=False, n_workers=2, threads_per_worker=3)
dask_client = Client(c)

application = get_wsgi_application()
