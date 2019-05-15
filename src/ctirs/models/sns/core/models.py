# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db.utils import OperationalError
from django.db import models
from django.utils.translation import ugettext_lazy

class Country(models.Model):
    name = models.CharField(max_length=128)
    alpha_2 = models.CharField(max_length=2)
    alpha_3 = models.CharField(max_length=3)
    country_code = models.IntegerField()
    iso_3166_2 = models.CharField(max_length=16)
    region = models.CharField(max_length=16)
    sub_region = models.CharField(max_length=32)
    region_code = models.IntegerField()
    sub_region_code = models.IntegerField()

    class Meta:
        db_table = 'stip_common_country'

    __country_tuple = None
    @classmethod
    def get_country_code_choices(cls):
        try:
            if cls.__country_tuple is None:
                r = []
                try:
                    for item in Country.objects.all().exclude(region='').order_by('name'):
                        r.append((item.alpha_2,ugettext_lazy(item.name)))
                except:
                    pass
                cls.__country_tuple = tuple(r)
            return cls.__country_tuple
        except OperationalError:
            #python magage.py migrate時に発生する
            return tuple([])

class Region(models.Model):
    country_code = models.CharField(max_length=2)
    administrative_area = models.CharField(max_length=128)
    code = models.CharField(max_length=16)

    class Meta:
        db_table = 'stip_common_region'
    
    def get_country_name(self):
        return Country.objects.get(alpha_2=self.country_code).name

    @staticmethod
    def get_country_codes():
        try:
            r = []
            try:
                for region in Region.objects.all().order_by('country_code'):
                    r.append(region.country_code)
            except:
                pass
            #重複を除き、アルファベット順で返却
            return sorted(list(set(r)))
        except OperationalError:
            #python magage.py migrate時に発生する
            return r
    
    @staticmethod
    def get_country_code_choices():
        r = []
        for item in Region.get_country_codes():
            r.append((item,ugettext_lazy(item)))
        return tuple(r)

    @staticmethod
    def get_administrative_areas(country_code):
        try:
            r = []
            try:
                for region in Region.objects.filter(country_code=country_code).order_by('code'):
                    r.append(region)
            except:
                pass
            return r
        except OperationalError:
            #python magage.py migrate時に発生する
            return r
    
    @staticmethod
    def get_administrative_areas_choices(country_code):
        r = []
        try:
            for item in Region.get_administrative_areas(country_code):
                r.append((item.code,ugettext_lazy(item.administrative_area)))
        except:
            pass
        return tuple(r)
