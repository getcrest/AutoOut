# Generated by Django 2.2.1 on 2019-08-13 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_experiment_treated_file_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='deleted_features',
            field=models.TextField(default='[]'),
        ),
    ]
