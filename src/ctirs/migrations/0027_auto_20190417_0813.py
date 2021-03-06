# Generated by Django 1.10.4 on 2019-04-16 23:13


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctirs', '0026_auto_20190303_1020'),
    ]

    operations = [
        migrations.AddField(
            model_name='snsconfig',
            name='attck_mongo_database',
            field=models.TextField(default=b'attck', max_length=64),
        ),
        migrations.AddField(
            model_name='snsconfig',
            name='attck_mongo_host',
            field=models.TextField(default=b'localhost', max_length=128),
        ),
        migrations.AddField(
            model_name='snsconfig',
            name='attck_mongo_port',
            field=models.IntegerField(default=27017),
        ),
        migrations.AlterField(
            model_name='snsconfig',
            name='gv_l2_url',
            field=models.TextField(default=b'', max_length=128),
        ),
    ]
