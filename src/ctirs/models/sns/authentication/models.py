# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Profile(models.Model):
    scan_csv = models.BooleanField(default=True)
    scan_pdf = models.BooleanField(default=False)
    scan_post = models.BooleanField(default=True)
    scan_txt = models.BooleanField(default=True)
    threat_actors = models.TextField(max_length=10240,default="")
    indicator_white_list = models.TextField(max_length=10240,default="")

    class Meta:
        db_table = 'stip_sns_user'

    def __str__(self):
        return str(self.id)

    @classmethod
    def create_first_login(cls):
        profile = Profile()
        profile.save()
        return profile
