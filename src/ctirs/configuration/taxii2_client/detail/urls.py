try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.configuration.taxii2_client.detail.views as detail

urlpatterns = [
    _url(r'^(?P<taxii_id>\S+)/resume/(?P<job_id>\S+)$', detail.resume),
    _url(r'^(?P<taxii_id>\S+)/pause/(?P<job_id>\S+)$', detail.pause),
    _url(r'^(?P<taxii_id>\S+)/remove/(?P<job_id>\S+)$', detail.remove),
    _url(r'^(?P<taxii_id>\S+)/create$', detail.create),
    _url(r'^(?P<taxii_id>\S+)/interval$', detail.interval),
    _url(r'^(?P<taxii_id>\S+)$', detail.top),
]
