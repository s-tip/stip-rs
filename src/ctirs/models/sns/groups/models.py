# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from ctirs.models import STIPUser

@python_2_unicode_compatible
class Group(models.Model):
    en_name = models.CharField(max_length=128,default=None,null=True,unique=True)
    local_name = models.CharField(max_length=128,default=None,null=True,unique=True)
    locale = models.CharField(max_length=4,choices=settings.LANGUAGES,default='en')
    description = models.TextField(max_length=1024,default=None,null=True)
    creator = models.ForeignKey(STIPUser)
    members = models.ManyToManyField(STIPUser,related_name='Members')

    class Meta:
        db_table = 'stip_common_group'
    
    def get_creator_url(self):
        return self.creator.get_url()

    def get_creator_picture(self):
        return self.creator.get_picture()
    
    def get_members_count(self):
        try:
            return self.members.count()
        except:
            return 0
    

    def __str__(self):
        return '%s (%s)' % (self.local_name,self.en_name)


    

