try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.isight.detail.views as detail

urlpatterns = [
    # adapter/isight/detail resume
    _url(r'^resume/(?P<job_id>\S+)$', detail.resume),
    # adapter/isight/detail pause
    _url(r'^pause/(?P<job_id>\S+)$', detail.pause),
    # adapter/isight/detail remove
    _url(r'^remove/(?P<job_id>\S+)$', detail.remove),
    # adapter/isight/detail create
    _url(r'^create$', detail.create),
    # adapter/isight/detail interval
    _url(r'^interval$', detail.interval),
    # adapter/isight/detail top
    _url(r'^$', detail.top),
]
