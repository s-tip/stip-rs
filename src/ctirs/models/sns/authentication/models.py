# -*- coding: utf-8 -*


from django.db import models


class Profile(models.Model):
    DEFAULT_PAHNTOM_SOURCE_NAME = 'local'
    DEFAULT_SPLUNK_API_PORT = 8089
    DEFAULT_SPLUNK_WEB_PORT = 8000
    SPLUNK_SCHEME_CHOICE = (
        ('http', 'http'),
        ('https', 'https')
    )

    scan_csv = models.BooleanField(default=True)
    scan_pdf = models.BooleanField(default=False)
    scan_post = models.BooleanField(default=True)
    scan_txt = models.BooleanField(default=True)
    threat_actors = models.TextField(max_length=10240, default="")
    indicator_white_list = models.TextField(max_length=10240, default="")
    phantom_host = models.TextField(max_length=128, default='')
    phantom_source_name = models.TextField(max_length=128, default=DEFAULT_PAHNTOM_SOURCE_NAME)
    phantom_playbook_name = models.TextField(max_length=128, default='')
    phantom_auth_token = models.TextField(max_length=128, default='')
    splunk_host = models.TextField(max_length=128, default='')
    splunk_api_port = models.IntegerField(default=DEFAULT_SPLUNK_API_PORT)
    splunk_web_port = models.IntegerField(default=DEFAULT_SPLUNK_WEB_PORT)
    splunk_username = models.TextField(max_length=128, default='')
    splunk_password = models.TextField(max_length=128, default='')
    splunk_scheme = models.TextField(max_length=16, default='https', choices=SPLUNK_SCHEME_CHOICE)
    splunk_query = models.TextField(max_length=10240, default='')

    class Meta:
        db_table = 'stip_sns_user'

    def __str__(self):
        return str(self.id)

    @classmethod
    def create_first_login(cls):
        profile = Profile()
        profile.save()
        return profile
