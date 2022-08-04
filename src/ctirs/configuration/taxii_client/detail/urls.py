try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii_client.detail.views as detail

urlpatterns = [
    # configuration/taxii_client/detail resume
    _url(r'^(?P<taxii_id>\S+)/resume/(?P<job_id>\S+)$', detail.resume),
    # configuration/taxii_client/detail pause
    _url(r'^(?P<taxii_id>\S+)/pause/(?P<job_id>\S+)$', detail.pause),
    # configuration/taxii_client/detail remove
    _url(r'^(?P<taxii_id>\S+)/remove/(?P<job_id>\S+)$', detail.remove),
    # configuration/taxii_client/detail create
    _url(r'^(?P<taxii_id>\S+)/create$', detail.create),
    # configuration/taxii_client/detail interval
    _url(r'^(?P<taxii_id>\S+)/interval$', detail.interval),
    # configuration/taxii_client/detail top
    _url(r'^(?P<taxii_id>\S+)$', detail.top),
]
