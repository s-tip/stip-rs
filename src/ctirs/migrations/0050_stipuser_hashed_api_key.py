# Generated by Django 4.1.1 on 2024-01-23 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctirs', '0049_alter_stipuser_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='stipuser',
            name='hashed_api_key',
            field=models.CharField(default='', max_length=1024),
        ),
    ]