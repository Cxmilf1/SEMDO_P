# Generated by Django 5.2.1 on 2025-06-15 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='persona',
            name='cedula',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
