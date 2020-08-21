from django.conf.urls import url
import ctirs.configuration.taxii2_client.detail.views as detail

urlpatterns = [
    url(r'^(?P<taxii_id>\S+)/resume/(?P<job_id>\S+)$', detail.resume),
    url(r'^(?P<taxii_id>\S+)/pause/(?P<job_id>\S+)$', detail.pause),
    url(r'^(?P<taxii_id>\S+)/remove/(?P<job_id>\S+)$', detail.remove),
    url(r'^(?P<taxii_id>\S+)/create$', detail.create),
    url(r'^(?P<taxii_id>\S+)/interval$', detail.interval),
    url(r'^(?P<taxii_id>\S+)$', detail.top),
]
