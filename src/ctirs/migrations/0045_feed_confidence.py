# Generated by Django 3.2.4 on 2022-02-17 02:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctirs', '0044_stipuser_confidence'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='confidence',
            field=models.IntegerField(default=50),
        ),
    ]
