# Generated by Django 3.2.4 on 2021-06-30 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctirs', '0042_auto_20210623_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feed',
            name='package_id',
            field=models.CharField(max_length=128, primary_key=True, serialize=False),
        ),
    ]