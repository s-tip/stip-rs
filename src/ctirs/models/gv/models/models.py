from django.db import models
from ctirs.models import STIPUser

####################


class TaxiiManager(models.Manager):
    def create(self, name, address='', port=0, ssl=False, path='', collection='', login_id='', login_password=''):
        t = Taxii()
        t.address = address
        t.name = name
        t.port = port
        t.ssl = ssl
        t.path = path
        t.collection = collection
        t.login_id = login_id
        t.login_password = login_password
        t.save()
        return

    def get_from_taxii_name(self, name):
        return self.get(name=name)


class Taxii(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    address = models.CharField(max_length=100, default='localhost')
    port = models.IntegerField(default=80)
    ssl = models.BooleanField(default=False)
    path = models.CharField(max_length=100, default='/taxii-data')
    collection = models.CharField(max_length=100, default='Default')
    login_id = models.CharField(max_length=100, default='login_id')
    login_password = models.CharField(max_length=100, default='login_password')

    objects = TaxiiManager()

    class Meta:
        db_table = 'stip_gv_taxii'

####################


class AliasesManager(models.Manager):
    def create(self, alias, stip_user, pid):
        t = Aliases()
        t.alias = alias
        t.user = stip_user
        if pid != '':
            t.id = pid
        t.save()
        return


class Aliases(models.Model):
    alias = models.CharField(max_length=10240)
    user = models.ForeignKey(STIPUser, default=None, on_delete=models.CASCADE, null=False)
    objects = AliasesManager()

    class Meta:
        db_table = 'stip_gv_aliases'

####################


class ConfigManager(models.Manager):
    def modify_system(self, default_taxii_name, path_sharing_policy_specifications='', path_bootstrap_css_dir='', ctirs_host=''):
        config = self.get()
        config.path_sharing_policy_specifications = path_sharing_policy_specifications
        config.path_bootstrap_css_dir = path_bootstrap_css_dir
        if len(default_taxii_name) != 0:
            taxii = Taxii.objects.get(name=default_taxii_name)
            config.default_taxii = taxii
        if len(ctirs_host) != 0:
            config.ctirs_host = ctirs_host
        config.save()

    def get_config(self):
        return self.get()


class Config(models.Model):
    DEFAULT_CTIRS_HOST = 'https://localhost:10001'
    path_upload_stix_dir = models.CharField(max_length=100, default='')
    path_sharing_policy_specifications = models.CharField(max_length=100, default='')
    path_bootstrap_css_dir = models.CharField(max_length=100, default='')
    default_taxii = models.ForeignKey(Taxii, default='', on_delete=models.SET_DEFAULT)
    ctirs_host = models.CharField(max_length=100, default=DEFAULT_CTIRS_HOST)
    objects = ConfigManager()

    class Meta:
        db_table = 'stip_gv_system'
