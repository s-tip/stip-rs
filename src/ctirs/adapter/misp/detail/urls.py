try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.misp.detail.views as detail

urlpatterns = [
    # adapter/misp/detail resume
    _url(r'^resume/(?P<job_id>\S+)$', detail.resume),
    # adapter/misp/detail pause
    _url(r'^pause/(?P<job_id>\S+)$', detail.pause),
    # adapter/misp/detail remove
    _url(r'^remove/(?P<job_id>\S+)$', detail.remove),
    # adapter/misp/detail create
    _url(r'^create$', detail.create),
    # adapter/misp/detail interval
    _url(r'^interval$', detail.interval),
    # adapter/misp/detail top
    _url(r'^$', detail.top),
]
