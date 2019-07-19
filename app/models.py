from django.db import models
from django.utils import timezone


class Dataset(models.Model):
    path = models.TextField(default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'datasets'


class Process(models.Model):
    """
    Processes:
    1. Detection
    2. Treatment
    """
    name = models.CharField(max_length=50, default='detection')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'processes'


class ProcessStatus(models.Model):
    """
    Statuses
    1. Not Started
    2. Running
    3. Completed
    4. Failed
    """
    name = models.CharField(max_length=100, default="Not Started")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'process_statuses'


class Experiment(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    process_status = models.ForeignKey(ProcessStatus, on_delete=models.CASCADE)
    results_path = models.TextField(default="")
    treated_file_path = models.TextField(default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'experiments'
