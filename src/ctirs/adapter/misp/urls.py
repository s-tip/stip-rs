from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.misp.detail.urls
import ctirs.adapter.misp.views as misp

urlpatterns = [
    # adapter/misp top
    _url(r'^$', misp.top),
    # adapter/misp modify
    _url(r'^modify$', misp.modify),
    # adapter/misp get
    _url(r'^get$', misp.get),
    # adapter/misp detail
    _url(r'^detail/', include(ctirs.adapter.misp.detail.urls)),
]
