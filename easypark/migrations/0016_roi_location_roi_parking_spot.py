# Generated by Django 5.0.6 on 2025-02-14 22:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("easypark", "0015_roi"),
    ]

    operations = [
        migrations.AddField(
            model_name="roi",
            name="location",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="easypark.parkinglocation",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="roi",
            name="parking_spot",
            field=models.OneToOneField(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="easypark.parkingspot",
            ),
            preserve_default=False,
        ),
    ]
