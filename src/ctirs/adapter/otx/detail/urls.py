try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.otx.detail.views as detail

urlpatterns = [
    # adapter/otx/detail resume
    _url(r'^resume/(?P<job_id>\S+)$', detail.resume),
    # adapter/otx/detail pause
    _url(r'^pause/(?P<job_id>\S+)$', detail.pause),
    # adapter/otx/detail remove
    _url(r'^remove/(?P<job_id>\S+)$', detail.remove),
    # adapter/otx/detail create
    _url(r'^create$', detail.create),
    # adapter/otx/detail interval
    _url(r'^interval$', detail.interval),
    # adapter/otx/detail top
    _url(r'^$', detail.top),
]
