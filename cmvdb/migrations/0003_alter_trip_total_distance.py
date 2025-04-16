# Generated by Django 5.2 on 2025-04-16 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmvdb', '0002_remove_trip_description_remove_trip_end_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='total_distance',
            field=models.FloatField(blank=True, help_text='Total distance of the trip in miles', null=True),
        ),
    ]
