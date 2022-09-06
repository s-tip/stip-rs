from django.conf.urls import include
try:
    from django.conf.urls import url as _url
except ImportError:
    from django.urls import re_path as _url
import ctirs.adapter.isight.detail.urls
import ctirs.adapter.isight.views as isight

urlpatterns = [
    # adapter/isight top
    _url(r'^$', isight.top),
    # adapter/isight modify
    _url(r'^modify$', isight.modify),
    # adapter/isight get
    _url(r'^get$', isight.get),
    # adapter/isght detail
    _url(r'^detail/', include(ctirs.adapter.isight.detail.urls)),
]
