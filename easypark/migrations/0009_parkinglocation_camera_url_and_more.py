# Generated by Django 5.0.6 on 2025-02-03 16:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("easypark", "0008_rename_created_at_reservation_completed_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="parkinglocation",
            name="camera_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="parkinglocation",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="parkinglocation",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="parking_images/"),
        ),
        migrations.AlterField(
            model_name="parkinglocation",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
